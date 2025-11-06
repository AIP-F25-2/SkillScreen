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
    
    
    async def process_resume_upload(self, files: List[Any], organization_id: str) -> Dict[str, Any]:
        """Process uploaded resume files"""
        try:
            # Generate upload ID and path
            upload_id = self.file_processor.generate_upload_id()
            upload_path = self.file_processor.create_upload_directory(upload_id)
            
            logger.info(f"Processing {len(files)} files for upload {upload_id}")
            
            # Process all files
            processed_files = await self._process_all_files(files, upload_path, upload_id)
            
            # Save candidates to database
            saved_candidates = self._save_candidates_to_database(processed_files, organization_id)
            
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
                # Handle ZIP files that return a list of processed files
                if isinstance(file_result, list):
                    processed_files.extend(file_result)
                else:
                    processed_files.append(file_result)
        
        return processed_files
    
    def _save_candidates_to_database(self, processed_files: List[Dict[str, Any]], organization_id: str) -> List[Dict[str, Any]]:
        """Save candidates to database"""
        saved_candidates = []
        logger.info(f"Checking {len(processed_files)} files for candidate saving...")
        
        for file_result in processed_files:
            if self._should_save_candidate(file_result):
                candidate_data = self._prepare_candidate_data(file_result, organization_id)
                save_result = self._save_single_candidate(candidate_data, file_result)
                if save_result:
                    saved_candidates.append(save_result)
        
        return saved_candidates
    
    def _should_save_candidate(self, file_result: Dict[str, Any]) -> bool:
        """Check if a file result should be saved as a candidate"""
        return (file_result.get('status') == 'processed' and 
                file_result.get('extracted_name') and 
                file_result.get('extracted_emails'))
    
    def _prepare_candidate_data(self, file_result: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        """Prepare candidate data for database"""
        return {
            'organization_id': organization_id,  # Use organization_id from request
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
    
    def _save_single_candidate(self, candidate_data: Dict[str, Any], file_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            
            # Handle ZIP files - extract and process all files inside
            if validation["file_type"] == "zip":
                zip_processed_files = self._process_zip_file(file_result, save_result["file_path"], upload_path)
                # Return list of processed files from ZIP (don't include ZIP file itself)
                return zip_processed_files if zip_processed_files else []
            
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
    
    def _process_zip_file(self, zip_file_result: Dict[str, Any], zip_file_path: str, upload_path: Path) -> List[Dict[str, Any]]:
        """Process ZIP file and extract individual files, returning list of processed resume files"""
        processed_files = []
        
        try:
            zip_path = Path(zip_file_path)
            logger.info(f"Extracting ZIP file: {zip_path}")
            
            # Extract files from ZIP
            extracted_files = self.file_processor.extract_zip_files(zip_path, upload_path)
            logger.info(f"Extracted {len(extracted_files)} files from ZIP")
            
            # Process each extracted file as a resume
            for extracted_file in extracted_files:
                try:
                    # Ignore macOS metadata files and folders (e.g., __MACOSX/, files starting with ._)
                    filename_lower = str(extracted_file.get("filename", "")).lower()
                    file_url_lower = str(extracted_file.get("url", "")).lower()
                    if (
                        filename_lower.startswith("._")
                        or "/__macosx/" in file_url_lower
                        or filename_lower.startswith("__macosx/")
                        or extracted_file.get("size", 0) == 0
                    ):
                        logger.info(f"Skipping macOS metadata/empty file from ZIP: {extracted_file.get('filename')}")
                        continue
                    # Check if file is a supported resume type
                    file_ext = Path(extracted_file["filename"]).suffix.lower()
                    if file_ext not in self.file_processor.SUPPORTED_EXTENSIONS:
                        logger.warning(f"Skipping unsupported file from ZIP: {extracted_file['filename']}")
                        # Include unsupported files in response with failed status
                        processed_files.append({
                            "filename": extracted_file["filename"],
                            "url": extracted_file["url"],
                            "size": extracted_file["size"],
                            "status": "failed",
                            "error": f"Unsupported file type: {file_ext}. Supported types: PDF, DOC, DOCX",
                            "source": "zip"
                        })
                        continue
                    
                    # Process the extracted resume file
                    processed_file = self._process_resume_file_sync(
                        {
                            "filename": extracted_file["filename"],
                            "url": extracted_file["url"],
                            "size": extracted_file["size"],
                            "status": "processed",
                            "source": "zip"
                        },
                        extracted_file["file_path"]
                    )
                    
                    if processed_file:
                        processed_files.append(processed_file)
                        if processed_file.get("status") == "processed":
                            logger.info(f"Successfully processed file from ZIP: {extracted_file['filename']}")
                        else:
                            logger.warning(f"Failed to process file from ZIP: {extracted_file['filename']}")
                    else:
                        # Include failed files in response
                        processed_files.append({
                            "filename": extracted_file["filename"],
                            "url": extracted_file["url"],
                            "size": extracted_file["size"],
                            "status": "failed",
                            "error": "Failed to process file",
                            "source": "zip"
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing extracted file {extracted_file['filename']}: {str(e)}")
                    # Include error in response
                    processed_files.append({
                        "filename": extracted_file.get("filename", "unknown"),
                        "url": extracted_file.get("url", ""),
                        "size": extracted_file.get("size", 0),
                        "status": "failed",
                        "error": str(e),
                        "source": "zip"
                    })
                    # Continue processing other files even if one fails
                    continue
            
            logger.info(f"ZIP file processed: {len(processed_files)} files successfully extracted and processed")
            return processed_files
            
        except Exception as e:
            logger.error(f"Error processing ZIP file {zip_file_result.get('filename')}: {str(e)}")
            # Return empty list if ZIP processing fails completely
            return []
    
    def _process_resume_file_sync(self, file_result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
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
