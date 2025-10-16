from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

class CandidateService:
    """Local candidate service for interview service"""
    
    def __init__(self):
        self.engine = None
        self.SessionFactory = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                self.engine = create_engine(db_url, echo=False)
                self.SessionFactory = sessionmaker(bind=self.engine)
                logger.info("Database connection initialized successfully")
            else:
                logger.error("DATABASE_URL not found")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new candidate"""
        if not self.engine:
            logger.error("Database not available")
            return {
                "success": False,
                "error": "Database not available",
                "data": None
            }
        
        try:
            session = self.SessionFactory()
            
            # Check if candidate already exists
            check_query = text("""
                SELECT id FROM candidates 
                WHERE organization_id = :org_id AND email = :email AND deleted_at IS NULL
            """)
            result = session.execute(check_query, {
                'org_id': candidate_data['organization_id'],
                'email': candidate_data['email']
            }).fetchone()
            
            if result:
                session.close()
                return {
                    "success": False,
                    "error": "Candidate with this email already exists",
                    "data": None
                }
            
            # Insert new candidate
            insert_query = text("""
                INSERT INTO candidates (organization_id, full_name, email, phone, location, resume_url, skills, experience, education, projects)
                VALUES (:org_id, :full_name, :email, :phone, :location, :resume_url, :skills, :experience, :education, :projects)
                RETURNING id, created_at
            """)
            
            result = session.execute(insert_query, {
                'org_id': candidate_data['organization_id'],
                'full_name': candidate_data['full_name'],
                'email': candidate_data['email'],
                'phone': candidate_data.get('phone'),
                'location': candidate_data.get('location'),
                'resume_url': candidate_data.get('resume_url'),
                'skills': candidate_data.get('skills'),
                'experience': candidate_data.get('experience'),
                'education': candidate_data.get('education'),
                'projects': candidate_data.get('projects')
            }).fetchone()
            
            session.commit()
            session.close()
            
            logger.info(f"Successfully saved candidate to database: {candidate_data['full_name']} - {candidate_data['email']}")
            
            return {
                "success": True,
                "data": {
                    "id": str(result[0]),
                    "full_name": candidate_data['full_name'],
                    "email": candidate_data['email'],
                    "created_at": result[1].isoformat() if result[1] else None
                },
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error saving candidate to database: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
