"""
Repository for InterviewToken database operations
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.interview_token import InterviewToken
from db import DBFactory


class InterviewTokenRepository:
    """Repository for managing interview tokens in database"""

    @staticmethod
    def create_token(
        token: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        session_id: str,
        interview_id: str,
        expires_at: datetime
    ) -> InterviewToken:
        """Create and store a new interview token"""
        db_session = DBFactory.get_session()
        try:
            interview_token = InterviewToken(
                token=token,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                session_id=session_id,
                interview_id=interview_id,
                expires_at=expires_at
            )
            db_session.add(interview_token)
            db_session.commit()
            return interview_token
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to create token: {str(e)}")
        finally:
            db_session.close()

    @staticmethod
    def get_token_by_token_string(token: str) -> Optional[InterviewToken]:
        """Get token record by token string"""
        db_session = DBFactory.get_session()
        try:
            interview_token = db_session.query(InterviewToken).filter(
                InterviewToken.token == token
            ).first()
            return interview_token
        finally:
            db_session.close()

    @staticmethod
    def validate_token(token: str) -> Optional[InterviewToken]:
        """Validate token (check if valid and not expired/used)"""
        db_session = DBFactory.get_session()
        try:
            interview_token = db_session.query(InterviewToken).filter(
                InterviewToken.token == token
            ).first()

            if not interview_token:
                return None

            # Check if token is valid
            if not interview_token.is_valid():
                return None

            return interview_token
        finally:
            db_session.close()

    @staticmethod
    def mark_token_used(token: str) -> bool:
        """Mark token as used"""
        db_session = DBFactory.get_session()
        try:
            interview_token = db_session.query(InterviewToken).filter(
                InterviewToken.token == token
            ).first()

            if not interview_token:
                return False

            interview_token.mark_used()
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to mark token as used: {str(e)}")
        finally:
            db_session.close()

    @staticmethod
    def get_token_by_candidate_id(candidate_id: str) -> Optional[InterviewToken]:
        """Get the most recent valid token for a candidate"""
        db_session = DBFactory.get_session()
        try:
            interview_token = db_session.query(InterviewToken).filter(
                InterviewToken.candidate_id == candidate_id
            ).order_by(InterviewToken.created_at.desc()).first()

            return interview_token
        finally:
            db_session.close()

    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from database"""
        db_session = DBFactory.get_session()
        try:
            now = datetime.now(timezone.utc)
            db_session.query(InterviewToken).filter(
                InterviewToken.expires_at < now
            ).delete()
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to cleanup expired tokens: {str(e)}")
        finally:
            db_session.close()
