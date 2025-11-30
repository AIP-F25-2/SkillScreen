import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import sys
import os
import uuid

from services.file_processor import FileProcessor
from services.text_extractor import TextExtractor
from services.email_extractor import EmailExtractor
from services.azure_resume_storage import AzureResumeStorage
from services.email_service import email_service
# Import local candidate service
from services.candidate_service import CandidateService

# Import database components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common-service'))
from db import DBFactory

logger = logging.getLogger(__name__)


class ResumeService:
    """Main service for handling resume uploads and processing"""

    def __init__(self, email_service_instance=None):
        self.file_processor = FileProcessor()
        self.text_extractor = TextExtractor()
        self.email_extractor = EmailExtractor()
        self.candidate_service = CandidateService()
        self.azure_storage = AzureResumeStorage()
        # Use injected email_service instance if provided, otherwise use default
        self.email_service = email_service_instance or email_service
    
    
    async def process_resume_upload(
        self, 
        files: List[Any], 
        organization_id: str, 
        job_position_id: str,
        interview_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process uploaded resume files"""
        try:
            # Generate upload ID and path
            upload_id = self.file_processor.generate_upload_id()
            upload_path = self.file_processor.create_upload_directory(upload_id)
            
            logger.info(f"Processing {len(files)} files for upload {upload_id}")
            
            # Process all files
            processed_files = await self._process_all_files(files, upload_path, upload_id)
            
            # Save candidates to database
            saved_candidates = self._save_candidates_to_database(
                processed_files, 
                organization_id, 
                job_position_id,
                interview_settings
            )
            
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
    
    def _save_candidates_to_database(
        self, 
        processed_files: List[Dict[str, Any]], 
        organization_id: str, 
        job_position_id: str,
        interview_settings: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Save candidates to database"""
        saved_candidates = []
        logger.info(f"Checking {len(processed_files)} files for candidate saving...")
        
        for file_result in processed_files:
            if self._should_save_candidate(file_result):
                candidate_data = self._prepare_candidate_data(file_result, organization_id)
                save_result = self._save_single_candidate(
                    candidate_data, 
                    file_result, 
                    job_position_id,
                    interview_settings
                )
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
        # Get extracted structured data
        skills = file_result.get('extracted_skills', [])
        experience = file_result.get('extracted_experience', [])
        education = file_result.get('extracted_education', [])
        projects = file_result.get('extracted_projects', [])
        
        return {
            'organization_id': organization_id,  # Use organization_id from request
            'full_name': file_result['extracted_name'],
            'email': file_result['extracted_emails'][0],  # Use first email
            'resume_url': file_result.get('url'),
            'phone': None,  # Could extract from resume text if needed
            'location': None,  # Could extract from resume text if needed
            'skills': skills if skills else None,  # Store as JSONB array
            'experience': experience if experience else None,  # Store as JSONB array
            'education': education if education else None,  # Store as JSONB array
            'projects': projects if projects else None  # Store as JSONB array
        }
    
    def _save_single_candidate(
        self, 
        candidate_data: Dict[str, Any], 
        file_result: Dict[str, Any], 
        job_position_id: str,
        interview_settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Save a single candidate to database, upload resume to Azure, and create interview record"""
        logger.info(f"File: {file_result.get('filename')}, Status: {file_result.get('status')}, Name: {file_result.get('extracted_name')}, Emails: {file_result.get('extracted_emails')}")
        
        result = self.candidate_service.create_candidate(candidate_data)
        
        if result['success']:
            candidate_id = result['data']['id']
            file_result['id'] = candidate_id
            logger.info(f"Saved candidate: {file_result['extracted_name']} - {file_result['extracted_emails'][0]} with ID: {candidate_id}")
            
            # Upload resume to Azure Blob Storage
            try:
                file_content = file_result.get('file_content')
                filename = file_result.get('filename')
                
                if file_content and filename:
                    azure_url = self.azure_storage.upload_resume(
                        file_content=file_content,
                        candidate_id=candidate_id,
                        filename=filename
                    )
                    logger.info(f"Uploaded resume to Azure: {azure_url}")
                    
                    # Update candidate record with Azure URL
                    self._update_candidate_resume_url(candidate_id, azure_url)
                else:
                    logger.warning(f"No file content available for Azure upload for candidate {candidate_id}")
            except Exception as e:
                logger.error(f"Failed to upload resume to Azure for candidate {candidate_id}: {str(e)}")
                # Don't fail the whole process if Azure upload fails
            
            # Create interview record automatically
            try:
                self._create_interview_for_candidate(
                    result['data'], 
                    candidate_data.get('organization_id'), 
                    job_position_id,
                    interview_settings
                )
            except Exception as e:
                logger.error(f"Failed to create interview record for candidate {candidate_id}: {str(e)}")
                # Don't fail the whole process if interview creation fails
            
            return result['data']
        else:
            self._handle_candidate_save_error(result, file_result)
            return None
    
    def _update_candidate_resume_url(self, candidate_id: str, azure_url: str) -> None:
        """Update candidate record with Azure resume URL"""
        try:
            from repository.candidate_repository import CandidateRepository
            session = DBFactory.get_session()
            try:
                candidate_repo = CandidateRepository(session)
                candidate_repo.update_candidate(candidate_id, {'resume_url': azure_url})
                session.commit()
                logger.info(f"Updated candidate {candidate_id} with Azure resume URL")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to update candidate resume URL: {str(e)}")
    
    def _create_interview_for_candidate(
        self, 
        candidate_data: Dict[str, Any], 
        organization_id: Optional[str], 
        job_position_id: str,
        interview_settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create an interview record automatically when a candidate is created"""
        try:
            from repository.interview_repository import InterviewRepository
            from repository.interview_template_repository import InterviewTemplateRepository
            session = DBFactory.get_session()
            try:
                interview_repo = InterviewRepository(session)
                template_repo = InterviewTemplateRepository(session)
                
                # Extract candidate_id - handle both dict with 'id' key and direct string
                candidate_id = candidate_data.get('id') if isinstance(candidate_data, dict) else str(candidate_data)
                if not candidate_id:
                    logger.warning("Cannot create interview: candidate ID is missing")
                    return
                
                # Ensure candidate_id is a string
                candidate_id = str(candidate_id)
                organization_id = organization_id or "e5d2d50b-6c07-43cd-8a78-ffd7b5b377bb"
                
                # Option 3: Query for organization's template (simple fallback)
                template = template_repo.get_template_by_organization(organization_id)
                if not template:
                    logger.error(f"No interview template found for organization {organization_id}. Please create a template first.")
                    raise ValueError(f"No interview template found for organization {organization_id}")
                
                template_id = str(template.id)
                logger.info(f"Using template {template_id} ({template.name}) for organization {organization_id}")
                
                # Generate session_id
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                session_id = f"session_{timestamp}_{uuid.uuid4().hex[:8]}"
                
                # Use provided settings or defaults
                mode = interview_settings.get('mode') if interview_settings and 'mode' in interview_settings else 'video'  # Default: video
                difficulty = interview_settings.get('difficulty') if interview_settings and 'difficulty' in interview_settings else 'medium'
                max_questions = interview_settings.get('max_questions') if interview_settings and 'max_questions' in interview_settings else 15
                interview_type = interview_settings.get('interview_type') if interview_settings and 'interview_type' in interview_settings else 'mixed'
                target_duration_minutes = interview_settings.get('target_duration_minutes') if interview_settings and 'target_duration_minutes' in interview_settings else 12
                
                # Create interview record with job_position_id and template_id
                interview_data = {
                    'organization_id': organization_id,
                    'job_position_id': job_position_id,  # Required field
                    'candidate_id': candidate_id,
                    'template_id': template_id,  # Required field
                    'status': 'scheduled',  # Start as scheduled
                    'mode': mode,  # Configurable, default: video
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    'settings': {
                        'difficulty': difficulty,
                        'session_id': session_id,
                        'max_questions': max_questions,
                        'interview_type': interview_type,
                        'candidate_record_id': candidate_id,
                        'target_duration_minutes': target_duration_minutes
                    }
                }
                
                interview = interview_repo.create_interview(interview_data)
                session.commit()
                interview_id = str(interview.id)

                logger.info(f"Created interview record {interview_id} for candidate {candidate_id} with job_position {job_position_id} and template {template_id} (mode: {mode})")

                # Send email invitation to candidate
                try:
                    candidate_name = candidate_data.get('full_name', 'Candidate')
                    candidate_email = candidate_data.get('email')

                    if candidate_email:
                        email_result = self.email_service.send_interview_invitation(
                            candidate_email=candidate_email,
                            candidate_name=candidate_name,
                            candidate_id=str(candidate_id),
                            session_id=session_id,
                            recruiter_name=None,
                            company_name=None,
                            expires_in_hours=48
                        )

                        logger.info(f"✅ Interview invitation email sent to {candidate_email} for interview {interview_id}")
                    else:
                        logger.warning(f"No email address available to send invitation for candidate {candidate_id}")
                except Exception as e:
                    logger.error(f"Failed to send invitation email for candidate {candidate_id}: {str(e)}")
                    # Don't fail the interview creation if email fails

            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error creating interview record: {str(e)}")
            raise
    
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
        # Strip out non-serializable / internal-only fields before returning to API
        safe_files: List[Dict[str, Any]] = []
        for f in processed_files:
            cleaned = dict(f)
            # Remove raw file bytes and local paths from API response
            cleaned.pop("file_content", None)
            cleaned.pop("file_path", None)
            safe_files.append(cleaned)

        return {
            "upload_id": upload_id,
            "status": "completed",
            "files_received": len(files),
            "files_processed": len(processed_files),
            "files": safe_files,
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
                "status": "processed",
                "file_content": file_content,  # Store for Azure upload
                "file_path": save_result["file_path"]  # Store local path
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
    
    def _process_resume_file_sync(self, file_result: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Process individual resume file and extract information"""
        try:
            # Read file content if not already present (for Azure upload)
            if 'file_content' not in file_result and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_result['file_content'] = f.read()
            
            # Extract text from file
            text_result = self.text_extractor.extract_text(file_path)
            
            if not text_result["success"]:
                file_result["status"] = "failed"
                file_result["error"] = text_result["error"]
                return file_result
            
            resume_text = text_result["text"]
            
            # Extract candidate information (name, email)
            candidate_info = self.email_extractor.extract_candidate_info(resume_text)
            
            # Extract structured data (skills, experience, education, projects)
            parsed_data = self._parse_resume_data(resume_text)
            
            # Update file result
            file_result.update({
                "extracted_emails": candidate_info["emails"],
                "extracted_name": candidate_info["name"],
                "email_count": candidate_info["email_count"],
                "extracted_skills": parsed_data.get("skills", []),
                "extracted_experience": parsed_data.get("experience", []),
                "extracted_education": parsed_data.get("education", []),
                "extracted_projects": parsed_data.get("projects", [])
            })
            
            logger.info(f"Processed {file_result['filename']}: "
                       f"emails={len(candidate_info['emails'])}, "
                       f"name={candidate_info['name']}, "
                       f"skills={len(parsed_data.get('skills', []))}, "
                       f"experience={len(parsed_data.get('experience', []))}")
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error processing resume file {file_path}: {str(e)}")
            file_result["status"] = "failed"
            file_result["error"] = str(e)
            return file_result
    
    def _parse_resume_data(self, text: str) -> Dict[str, Any]:
        """Parse resume text to extract skills, experience, education, and projects"""
        import re
        
        result = {
            "skills": [],
            "experience": [],
            "education": [],
            "projects": []
        }
        
        text_lower = text.lower()
        
        # Extract skills (common technical skills)
        skills_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'laravel',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops',
            'machine learning', 'ai', 'tensorflow', 'pytorch', 'scikit-learn',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum',
            'linux', 'unix', 'bash', 'powershell', 'shell scripting',
            'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'swift',
            'android', 'ios', 'react native', 'flutter', 'xamarin'
        ]
        
        found_skills = []
        for skill in skills_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        result["skills"] = list(set(found_skills))  # Remove duplicates
        
        # Extract experience (look for date patterns and job titles)
        experience_pattern = re.compile(
            r'(\d{4}|\w+\s+\d{4})\s*[-–]\s*(\d{4}|\w+\s+\d{4}|\bpresent\b|\bcurrent\b)',
            re.IGNORECASE
        )
        experience_matches = experience_pattern.findall(text)
        if experience_matches:
            result["experience"] = [{"period": f"{start} - {end}"} for start, end in experience_matches[:5]]
        
        # Extract education (look for degree keywords and institutions)
        education_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma', 'certificate']
        education_section = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                # Try to get institution from nearby lines
                institution = ""
                if i + 1 < len(lines):
                    institution = lines[i + 1].strip()
                education_section.append({
                    "degree": line.strip(),
                    "institution": institution
                })
        result["education"] = education_section[:5]  # Limit to 5
        
        # Extract projects (look for "project" keyword)
        project_pattern = re.compile(r'(?:project|portfolio|work)[\s:]+(.+?)(?:\n|$)', re.IGNORECASE)
        project_matches = project_pattern.findall(text)
        if project_matches:
            result["projects"] = [{"name": match.strip()} for match in project_matches[:5]]
        
        return result
