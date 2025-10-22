from typing import List, Optional, Dict, Any
from repository.candidate_repository import CandidateRepository
from models.candidate import Candidate
from db import UnitOfWork
import logging

logger = logging.getLogger(__name__)

# Constants
CANDIDATE_NOT_FOUND_ERROR = "Candidate not found"

class CandidateService:
    """Service layer for candidate operations"""
    
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
    
    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Get candidate by ID"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                candidate = repo.get_candidate_by_id(candidate_id)
                
                if not candidate:
                    return {
                        "success": False,
                        "error": CANDIDATE_NOT_FOUND_ERROR,
                        "data": None
                    }
                
                return {
                    "success": True,
                    "data": candidate.to_dict(),
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error getting candidate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def get_candidates_by_organization(self, organization_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get all candidates for an organization"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                candidates = repo.get_candidates_by_organization(organization_id, limit, offset)
                
                return {
                    "success": True,
                    "data": [candidate.to_dict() for candidate in candidates],
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error getting candidates: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def update_candidate(self, candidate_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate information"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                candidate = repo.update_candidate(candidate_id, update_data)
                
                if not candidate:
                    return {
                        "success": False,
                        "error": CANDIDATE_NOT_FOUND_ERROR,
                        "data": None
                    }
                
                return {
                    "success": True,
                    "data": candidate.to_dict(),
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error updating candidate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def delete_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Delete candidate (soft delete)"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                success = repo.soft_delete_candidate(candidate_id)
                
                if not success:
                    return {
                        "success": False,
                        "error": CANDIDATE_NOT_FOUND_ERROR,
                        "data": None
                    }
                
                return {
                    "success": True,
                    "data": {"message": "Candidate deleted successfully"},
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error deleting candidate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def search_candidates(self, organization_id: str, search_term: str, limit: int = 50) -> Dict[str, Any]:
        """Search candidates by name or email"""
        try:
            with self.uow:
                repo = CandidateRepository(self.uow.session)
                candidates = repo.search_candidates(organization_id, search_term, limit)
                
                return {
                    "success": True,
                    "data": [candidate.to_dict() for candidate in candidates],
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error searching candidates: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
