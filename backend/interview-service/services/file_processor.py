import os
import zipfile
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import aiofiles

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file processing operations for resume uploads"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ZIP_SIZE = 50 * 1024 * 1024   # 50MB
    
    def __init__(self, temp_dir: str = "temp/resumes"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_upload_id(self) -> str:
        """Generate unique upload ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"upload_{timestamp}"
    
    def create_upload_directory(self, upload_id: str) -> Path:
        """Create directory for upload"""
        upload_path = self.temp_dir / upload_id
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path
    
    def validate_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate uploaded file"""
        result = {
            "valid": True,
            "error": None,
            "file_type": None
        }
        
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            result["valid"] = False
            result["error"] = f"File size {file_size} exceeds maximum allowed size {self.MAX_FILE_SIZE}"
            return result
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext == '.zip':
            result["file_type"] = "zip"
        elif file_ext in self.SUPPORTED_EXTENSIONS:
            result["file_type"] = "resume"
        else:
            result["valid"] = False
            result["error"] = f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}, .zip"
        
        return result
    
    async def save_file(self, file_content: bytes, filename: str, upload_path: Path) -> Dict[str, Any]:
        """Save uploaded file to disk"""
        try:
            file_path = upload_path / filename
            
            # Write file content using async file operations
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "url": f"/temp/resumes/{upload_path.name}/{filename}",
                "size": len(file_content)
            }
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_zip_files(self, zip_path: Path, upload_path: Path) -> List[Dict[str, Any]]:
        """Extract files from ZIP archive"""
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check total extracted size
                total_size = sum(info.file_size for info in zip_ref.infolist())
                if total_size > self.MAX_ZIP_SIZE:
                    raise ValueError(f"ZIP contents exceed maximum size {self.MAX_ZIP_SIZE}")
                
                for file_info in zip_ref.infolist():
                    # Skip directories and hidden files
                    if file_info.is_dir() or file_info.filename.startswith('.'):
                        continue
                    
                    # Check individual file size
                    if file_info.file_size > self.MAX_FILE_SIZE:
                        logger.warning(f"Skipping large file in ZIP: {file_info.filename}")
                        continue
                    
                    # Extract file
                    extracted_content = zip_ref.read(file_info.filename)
                    filename = Path(file_info.filename).name
                    
                    # Save extracted file
                    extracted_path = upload_path / filename
                    with open(extracted_path, 'wb') as f:
                        f.write(extracted_content)
                    
                    extracted_files.append({
                        "filename": filename,
                        "file_path": str(extracted_path),
                        "url": f"/temp/resumes/{upload_path.name}/{filename}",
                        "size": file_info.file_size,
                        "source": "zip"
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting ZIP file: {str(e)}")
            raise
        
        return extracted_files
    
    def cleanup_upload(self, upload_id: str) -> bool:
        """Clean up upload directory"""
        try:
            upload_path = self.temp_dir / upload_id
            if upload_path.exists():
                shutil.rmtree(upload_path)
                logger.info(f"Cleaned up upload directory: {upload_path}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up upload {upload_id}: {str(e)}")
        
        return False
