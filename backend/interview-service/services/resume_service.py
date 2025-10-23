import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys
import os

from services.file_processor import FileProcessor
from services.text_extractor import TextExtractor
from services.email_extractor import EmailExtractor
# Import local candidate service
from services.candidate_service import CandidateService

logger = logging.getLogger(__name__)


class ResumeService:
    """Main service for handling resume uploads and processing"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
        self.text_extractor = TextExtractor()
        self.email_extractor = EmailExtractor()
        self.candidate_service = CandidateService()
    
    
    async def process_resume_upload(self, files: List[Any]) -> Dict[str, Any]:
        """Process uploaded resume files"""
        try:
            # Generate upload ID and path
            upload_id = self.file_processor.generate_upload_id()
            upload_path = self.file_processor.create_upload_directory(upload_id)
            
            logger.info(f"Processing {len(files)} files for upload {upload_id}")
            
            # Process all files
            processed_files = await self._process_all_files(files, upload_path, upload_id)
            
            # Save candidates to database
            saved_candidates = await self._save_candidates_to_database(processed_files)
            
            # Prepare response data
            response_data = self._prepare_response_data(upload_id, files, processed_files, saved_candidates)
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"Error processing resume upload: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def _process_all_files(self, files: List[Any], upload_path: Path, upload_id: str) -> List[Dict[str, Any]]:
        """Process all uploaded files"""
        processed_files = []
        
        for file in files:
            file_result = await self._process_single_file(file, upload_path, upload_id)
            if file_result:
                processed_files.append(file_result)
        
        return processed_files
    
    async def _save_candidates_to_database(self, processed_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save candidates to database"""
        saved_candidates = []
        logger.info(f"Checking {len(processed_files)} files for candidate saving...")
        
        for file_result in processed_files:
            if self._should_save_candidate(file_result):
                candidate_data = self._prepare_candidate_data(file_result)
                save_result = await self._save_single_candidate(candidate_data, file_result)
                if save_result:
                    saved_candidates.append(save_result)
        
        return saved_candidates
    
    def _should_save_candidate(self, file_result: Dict[str, Any]) -> bool:
        """Check if a file result should be saved as a candidate"""
        return (file_result.get('status') == 'processed' and 
                file_result.get('extracted_name') and 
                file_result.get('extracted_emails'))
    
    def _prepare_candidate_data(self, file_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare candidate data for database"""
        return {
            'organization_id': '25cfc4a5-136f-4bd8-9ec1-5778c78cded2',  # Default organization ID
            'full_name': file_result['extracted_name'],
            'email': file_result['extracted_emails'][0],  # Use first email
            'resume_url': file_result.get('url'),
            'phone': None,
            'location': None,
            'skills': None,
            'experience': None,
            'education': None,
            'projects': None
        }
    
    async def _save_single_candidate(self, candidate_data: Dict[str, Any], file_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save a single candidate to database"""
        logger.info(f"File: {file_result.get('filename')}, Status: {file_result.get('status')}, Name: {file_result.get('extracted_name')}, Emails: {file_result.get('extracted_emails')}")
        
        result = self.candidate_service.create_candidate(candidate_data)
        
        if result['success']:
            file_result['id'] = result['data']['id']
            logger.info(f"Saved candidate: {file_result['extracted_name']} - {file_result['extracted_emails'][0]} with ID: {result['data']['id']}")
            return result['data']
        else:
            self._handle_candidate_save_error(result, file_result)
            return None
    
    def _handle_candidate_save_error(self, result: Dict[str, Any], file_result: Dict[str, Any]) -> None:
        """Handle candidate save errors"""
        logger.warning(f"Failed to save candidate: {result['error']}")
        file_result['candidate_save_error'] = result['error']
        
        # Check if it's a unique constraint error
        if "Database constraint: Only one candidate per email address is allowed" in result['error']:
            file_result['status'] = 'duplicate_email'
            logger.info(f"Candidate with email {file_result['extracted_emails'][0]} already exists - marked as duplicate")
    
    def _prepare_response_data(self, upload_id: str, files: List[Any], processed_files: List[Dict[str, Any]], saved_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare response data"""
        return {
            "upload_id": upload_id,
            "status": "completed",
            "files_received": len(files),
            "files_processed": len(processed_files),
            "files": processed_files,
            "candidates_saved": len(saved_candidates),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_single_file(self, file: Any, upload_path: Path, upload_id: str) -> Optional[Dict[str, Any]]:
        """Process a single uploaded file"""
        try:
            filename = file.filename
            file_content = await file.read()
            
            logger.info(f"Processing file: {filename} ({len(file_content)} bytes)")
            
            # Validate file
            validation = self.file_processor.validate_file(filename, len(file_content))
            if not validation["valid"]:
                logger.warning(f"File validation failed for file: {validation['error']}")
                return {
                    "filename": filename,
                    "status": "failed",
                    "error": validation["error"],
                    "size": len(file_content)
                }
            
            # Save file
            save_result = await self.file_processor.save_file(file_content, filename, upload_path)
            if not save_result["success"]:
                logger.error(f"Failed to save file: {save_result['error']}")
                return {
                    "filename": filename,
                    "status": "failed",
                    "error": save_result["error"],
                    "size": len(file_content)
                }
            
            file_result = {
                "filename": filename,
                "url": save_result["url"],
                "size": save_result["size"],
                "status": "processed"
            }
            
            # Handle ZIP files
            if validation["file_type"] == "zip":
                return self._process_zip_file(file_result, upload_path)
            
            # Process resume file
            return self._process_resume_file_sync(file_result, save_result["file_path"])
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            return {
                "filename": file.filename,
                "status": "failed",
                "error": str(e),
                "size": len(file_content) if 'file_content' in locals() else 0
            }
    
    def _process_zip_file(self, file_result: Dict[str, Any], upload_path: Path) -> Dict[str, Any]:
        """Process ZIP file and extract individual files"""
        try:
            zip_path = Path(file_result["url"].replace("/temp/resumes/", "temp/resumes/"))
            
            # Extract files from ZIP
            extracted_files = self.file_processor.extract_zip_files(zip_path, upload_path)
            
            # Process each extracted file
            processed_files = []
            
            for extracted_file in extracted_files:
                if self.text_extractor.is_text_extractable(extracted_file["file_path"]):
                    processed_file = self._process_resume_file_sync(extracted_file, extracted_file["file_path"])
                    if processed_file:
                        processed_files.append(processed_file)
            
            # ZIP files are processed, no additional fields needed
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error processing ZIP file: {str(e)}")
            file_result["status"] = "failed"
            file_result["error"] = str(e)
            return file_result
    
    def _process_resume_file(self, file_result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Process individual resume file and extract information"""
        try:
            # Extract text from file
            text_result = self.text_extractor.extract_text(file_path)
            
            if not text_result["success"]:
                file_result["status"] = "failed"
                file_result["error"] = text_result["error"]
                return file_result
            
            # Extract candidate information
            candidate_info = self.email_extractor.extract_candidate_info(text_result["text"])
            
            # Update file result
            file_result.update({
                "extracted_emails": candidate_info["emails"],
                "extracted_name": candidate_info["name"],
                "email_count": candidate_info["email_count"]
            })
            
            logger.info(f"Processed {file_result['filename']}: "
                       f"emails={len(candidate_info['emails'])}, "
                       f"name={candidate_info['name']}")
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error processing resume file {file_path}: {str(e)}")
            file_result["status"] = "failed"
            file_result["error"] = str(e)
            return file_result
    
    def _process_resume_file_sync(self, file_result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Process individual resume file and extract information (synchronous version)"""
        try:
            # Extract text from file
            text_result = self.text_extractor.extract_text(file_path)
            
            if not text_result["success"]:
                file_result["status"] = "failed"
                file_result["error"] = text_result["error"]
                return file_result
            
            # Extract candidate information
            candidate_info = self.email_extractor.extract_candidate_info(text_result["text"])
            
            # Update file result
            file_result.update({
                "extracted_emails": candidate_info["emails"],
                "extracted_name": candidate_info["name"],
                "email_count": candidate_info["email_count"]
            })
            
            logger.info(f"Processed {file_result['filename']}: "
                       f"emails={len(candidate_info['emails'])}, "
                       f"name={candidate_info['name']}")
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error processing resume file {file_path}: {str(e)}")
            file_result["status"] = "failed"
            file_result["error"] = str(e)
            return file_result
