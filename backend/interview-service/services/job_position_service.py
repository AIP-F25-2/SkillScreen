from typing import Dict, Any, List, Optional
import logging
import os
import sys

# Import local modules
from repository.job_position_repository import JobPositionRepository
from models.job_position import JobPosition

# Add common-service to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common-service'))

from db import UnitOfWork

logger = logging.getLogger(__name__)

class JobPositionService:
    """Service layer for job position operations using common-service components"""
    
    def __init__(self):
        self.uow = UnitOfWork()
    
    def create_job_position(self, job_position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job position"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                
                # Validate required fields
                if not job_position_data.get('organization_id'):
                    return {
                        "success": False,
                        "error": "organization_id is required",
                        "data": None
                    }
                
                if not job_position_data.get('title'):
                    return {
                        "success": False,
                        "error": "title is required",
                        "data": None
                    }
                
                # Create job position
                job_position = repo.create_job_position(job_position_data)
                
                logger.info(f"Successfully created job position: {job_position_data['title']} with ID: {job_position.id}")
                
                return {
                    "success": True,
                    "data": job_position.to_dict(),
                    "error": None
                }
                
        except ValueError as e:
            logger.error(f"Validation error creating job position: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid UUID format: {str(e)}",
                "data": None
            }
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error creating job position: {error_str}")
            return {
                "success": False,
                "error": f"Database error: {error_str}",
                "data": None
            }
    
    def get_job_position_by_id(self, job_position_id: str) -> Dict[str, Any]:
        """Get job position by ID"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                job_position = repo.get_job_position_by_id(job_position_id)
                
                if not job_position:
                    return {
                        "success": False,
                        "error": "Job position not found",
                        "data": None
                    }
                
                return {
                    "success": True,
                    "data": job_position.to_dict(),
                    "error": None
                }
                
        except ValueError as e:
            logger.error(f"Invalid UUID format: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid job position ID format: {str(e)}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Error getting job position: {str(e)}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None
            }
    
    def get_job_positions(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get job positions for an organization"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                
                job_positions = repo.get_job_positions_by_organization(
                    organization_id=organization_id,
                    limit=limit,
                    offset=offset,
                    is_active=is_active
                )
                
                total = repo.count_job_positions_by_organization(
                    organization_id=organization_id,
                    is_active=is_active
                )
                
                return {
                    "success": True,
                    "data": {
                        "job_positions": [jp.to_dict() for jp in job_positions],
                        "total": total,
                        "limit": limit,
                        "offset": offset
                    },
                    "error": None
                }
                
        except ValueError as e:
            logger.error(f"Invalid UUID format: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid organization ID format: {str(e)}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Error getting job positions: {str(e)}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None
            }
    
    def get_all_job_positions(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = True
    ) -> Dict[str, Any]:
        """Get all job positions across all organizations"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                
                job_positions = repo.get_all_job_positions(
                    limit=limit,
                    offset=offset,
                    is_active=is_active
                )
                
                total = repo.count_all_job_positions(is_active=is_active)
                
                return {
                    "success": True,
                    "data": {
                        "job_positions": [jp.to_dict() for jp in job_positions],
                        "total": total,
                        "limit": limit,
                        "offset": offset
                    },
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error getting all job positions: {str(e)}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None
            }
    
    def update_job_position(self, job_position_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update job position"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                
                job_position = repo.update_job_position(job_position_id, update_data)
                
                if not job_position:
                    return {
                        "success": False,
                        "error": "Job position not found",
                        "data": None
                    }
                
                logger.info(f"Successfully updated job position: {job_position_id}")
                
                return {
                    "success": True,
                    "data": job_position.to_dict(),
                    "error": None
                }
                
        except ValueError as e:
            logger.error(f"Invalid UUID format: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid job position ID format: {str(e)}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Error updating job position: {str(e)}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None
            }
    
    def delete_job_position(self, job_position_id: str) -> Dict[str, Any]:
        """Soft delete a job position"""
        try:
            with self.uow:
                repo = JobPositionRepository(self.uow.session)
                
                success = repo.soft_delete_job_position(job_position_id)
                
                if not success:
                    return {
                        "success": False,
                        "error": "Job position not found",
                        "data": None
                    }
                
                logger.info(f"Successfully deleted job position: {job_position_id}")
                
                return {
                    "success": True,
                    "data": {"message": "Job position deleted successfully"},
                    "error": None
                }
                
        except ValueError as e:
            logger.error(f"Invalid UUID format: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid job position ID format: {str(e)}",
                "data": None
            }
        except Exception as e:
            logger.error(f"Error deleting job position: {str(e)}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "data": None
            }


