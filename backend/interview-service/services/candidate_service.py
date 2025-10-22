from typing import Dict, Any
import sys
import logging

# Add common-service to path
sys.path.append("/common-service")

# Import common-service modules directly
from repository.candidate_repository import CandidateRepository
from models.candidate import Candidate
from db import UnitOfWork

logger = logging.getLogger(__name__)

class CandidateService:
    """Service layer for candidate operations using common-service components"""
    
    def __init__(self):
        self.uow = UnitOfWork()
    
    def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new candidate"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                
                # Check if candidate already exists
                if repo.candidate_exists(candidate_data['organization_id'], candidate_data['email']):
                    logger.warning(f"Candidate with email {candidate_data['email']} already exists")
                    return {
                        "success": False,
                        "error": "Candidate with this email already exists",
                        "data": None
                    }
                
                candidate = repo.create_candidate(candidate_data)
                
                logger.info(f"Successfully saved candidate to database: {candidate_data['full_name']} - {candidate_data['email']}")
                
                return {
                    "success": True,
                    "data": candidate.to_dict(),
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error creating candidate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }