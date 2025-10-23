from typing import Dict, Any
import logging

# Import local modules
from repository.candidate_repository import CandidateRepository
from models.candidate import Candidate
import os
import sys

# Add common-service to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common-service'))

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
                
                # Try to create candidate (may fail due to unique constraint)
                candidate = repo.create_candidate(candidate_data)
                
                logger.info(f"Successfully saved candidate to database: {candidate_data['full_name']} - {candidate_data['email']} with ID: {candidate.id}")
                
                return {
                    "success": True,
                    "data": candidate.to_dict(),
                    "error": None
                }
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error creating candidate: {error_str}")
            
            # Check if it's a unique constraint violation
            if "duplicate key value violates unique constraint" in error_str and "uq_candidates_org_email" in error_str:
                # Database has unique constraint - this is expected behavior
                # We'll return a specific error message
                return {
                    "success": False,
                    "error": "Database constraint: Only one candidate per email address is allowed. Please use a different email or contact support to update existing candidate.",
                    "data": None
                }
            else:
                # Other database errors
                return {
                    "success": False,
                    "error": f"Database error: {error_str}",
                    "data": None
                }