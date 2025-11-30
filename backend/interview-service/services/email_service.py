"""
Email service for sending interview invitations using Resend
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import resend

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv("RESEND_API_KEY", "")

# Import token repository for database persistence
from repository.interview_token_repository import InterviewTokenRepository

class EmailService:
    """Service for sending interview invitation emails"""

    def __init__(self, token_store=None):
        self.from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.email_mode = os.getenv("EMAIL_MODE", "production")  # test or production
        self.test_email_redirect = os.getenv("TEST_EMAIL_REDIRECT", "")  # Redirect test emails to this address
        self.token_store = token_store or {}  # Reference to token store for persisting tokens
    
    def generate_interview_token(self) -> str:
        """Generate a secure random token for interview access"""
        return secrets.token_urlsafe(32)
    
    def send_interview_invitation(
        self,
        candidate_email: str,
        candidate_name: str,
        candidate_id: str,
        session_id: str,
        recruiter_name: Optional[str] = None,
        company_name: Optional[str] = None,
        expires_in_hours: int = 48
    ) -> dict:
        """
        Send an interview invitation email to a candidate
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's full name
            candidate_id: Unique candidate identifier
            session_id: Interview session ID
            recruiter_name: Name of the recruiter (optional)
            company_name: Name of the company (optional)
            expires_in_hours: Token expiration time in hours (default 48)
        
        Returns:
            dict: Response from Resend API
        """
        try:
            # Generate unique token
            token = self.generate_interview_token()
            
            # Create interview link
            interview_link = f"{self.base_url}/interview-link?token={token}"
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            # Prepare email content
            subject = f"Interview Invitation for {candidate_name} - {company_name or 'SkillScreen'}"
            
            html_content = self._build_invitation_email_html(
                candidate_name=candidate_name,
                interview_link=interview_link,
                recruiter_name=recruiter_name,
                company_name=company_name,
                expires_at=expires_at,
                original_email=None  # No longer redirecting
            )
            
            # Determine recipient email (redirect in test mode if configured)
            recipient_email = candidate_email
            redirect_note = ""
            if self.email_mode == "test" and self.test_email_redirect:
                recipient_email = self.test_email_redirect
                redirect_note = f" (redirected from {candidate_email})"

            # Send email via Resend
            response = resend.Emails.send({
                "from": self.from_email,
                "to": recipient_email,
                "subject": subject,
                "html": html_content,
            })

            mode_str = f"[{self.email_mode.upper()}]" if self.email_mode == "test" else ""
            logger.info(f"✅ Interview invitation sent {mode_str} to {recipient_email}{redirect_note} (session: {session_id}, token expires: {expires_at.isoformat()})")

            # Store token in database for persistence
            try:
                expires_at_utc = expires_at.replace(tzinfo=None)  # Convert to naive datetime if needed
                InterviewTokenRepository.create_token(
                    token=token,
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    session_id=session_id,
                    interview_id=None,  # Interview ID will be set during validation
                    expires_at=expires_at_utc
                )
                logger.info(f"✅ Token stored in database (token: {token[:20]}...)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to store token in database: {str(e)}")
                # Continue anyway - token is still in memory
                if self.token_store is not None:
                    self.token_store[token] = {
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "candidate_email": candidate_email,
                        "session_id": session_id,
                        "expires_at": expires_at.isoformat()
                    }
                    logger.info(f"✅ Token stored in memory (token: {token[:20]}...)")

            return {
                "success": True,
                "email_id": response.get("id"),
                "token": token,
                "expires_at": expires_at.isoformat(),
                "session_id": session_id,
                "candidate_id": candidate_id,
                "candidate_email": candidate_email,
                "candidate_name": candidate_name
            }
            
        except Exception as e:
            logger.error(f"Failed to send interview invitation: {str(e)}")
            raise Exception(f"Failed to send email: {str(e)}")
    
    def send_interview_completion_notification(
        self,
        recruiter_email: str,
        recruiter_name: str,
        candidate_name: str,
        interview_id: str,
        session_id: str
    ) -> dict:
        """
        Send a notification to recruiter when candidate completes interview
        
        Args:
            recruiter_email: Recruiter's email address
            recruiter_name: Recruiter's full name
            candidate_name: Candidate's name
            interview_id: Completed interview ID
            session_id: Interview session ID
        
        Returns:
            dict: Response from Resend API
        """
        try:
            # Create summary link
            summary_link = f"{self.base_url}/interview-summary?id={session_id}"
            
            subject = f"Interview Completed - {candidate_name}"
            
            html_content = self._build_completion_email_html(
                recruiter_name=recruiter_name,
                candidate_name=candidate_name,
                summary_link=summary_link,
                interview_id=interview_id
            )
            
            # Send email via Resend
            response = resend.Emails.send({
                "from": self.from_email,
                "to": recruiter_email,
                "subject": subject,
                "html": html_content,
            })
            
            logger.info(f"Completion notification sent to {recruiter_email} for interview {interview_id}")
            
            return {
                "success": True,
                "email_id": response.get("id"),
                "interview_id": interview_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send completion notification: {str(e)}")
            raise Exception(f"Failed to send notification: {str(e)}")
    
    def _build_invitation_email_html(
        self,
        candidate_name: str,
        interview_link: str,
        recruiter_name: Optional[str],
        company_name: Optional[str],
        expires_at: datetime,
        original_email: Optional[str] = None
    ) -> str:
        """Build HTML content for interview invitation email"""
        
        recruiter_text = f"{recruiter_name} from " if recruiter_name else ""
        company_text = company_name or "SkillScreen"
        
        # Add original email info if provided (for testing)
        original_email_section = ""
        if original_email:
            original_email_section = f"""
                                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 18px 20px; margin: 24px 0; border-radius: 12px;">
                                        <p style="margin: 0; color: rgba(255, 255, 255, 0.76); font-size: 13px; line-height: 1.6;">
                                            <span style="color: #ffffff; font-weight: 600;">Original Recipient:</span> {original_email}<br>
                                            <span style="color: rgba(255, 255, 255, 0.6);">Redirected internally for testing</span>
                                        </p>
                                    </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interview Invitation</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #050505; color: #ffffff;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #050505;">
                <tr>
                    <td align="center" style="padding: 48px 20px;">
                        <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 32px 32px 0; text-align: left;">
                                   
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: -0.03em;">
                                        Interview Invitation
                                    </h1>

                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 32px;">
                                    <p style="margin: 0 0 24px; color: #ffffff; font-size: 17px; line-height: 1.6; font-weight: 400;">
                                        Hello <strong style="font-weight: 600;">{candidate_name}</strong>,
                                    </p>
                                    
                                    {original_email_section}
                                    
                                    <p style="margin: 0 0 24px; color: rgba(255, 255, 255, 0.82); font-size: 16px; line-height: 1.6; font-weight: 400;">
                                        {recruiter_text}<strong style="font-weight: 600; color: #ffffff;">{company_text}</strong> has invited you to complete an AI-powered interview experience.
                                    </p>
                                    
                                    <div style="margin: 0 0 32px; padding: 24px; background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02)); border: 1px solid rgba(255, 255, 255, 0.09); border-radius: 16px;">
                                        <p style="margin: 0 0 16px; color: rgba(255, 255, 255, 0.7); font-size: 14px; line-height: 1.6;">
                                            This secure link takes you directly to your personalized interview space. Please use a modern browser and ensure your camera and microphone are enabled.
                                        </p>
                                        <a href="{interview_link}" 
                                           style="display: inline-block; padding: 14px 26px; background-color: #ffffff; color: #050505; text-decoration: none; font-size: 14px; font-weight: 600; border-radius: 999px; letter-spacing: 0.01em;">
                                            Start Interview
                                        </a>
                                    </div>
                                    
                                    <!-- Important Info -->
                                    <div style="margin: 32px 0; padding: 24px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;">
                                        <h3 style="margin: 0 0 16px; color: #ffffff; font-size: 14px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;">
                                            Key Details
                                        </h3>
                                        <ul style="margin: 0; padding-left: 18px; color: rgba(255, 255, 255, 0.75); font-size: 14px; line-height: 1.8; font-weight: 400;">
                                            <li style="margin-bottom: 10px;">Link expires <strong style="color: #ffffff; font-weight: 600;">{expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}</strong></li>
                                            <li style="margin-bottom: 10px;">One-time access—avoid refreshing or closing the browser mid-interview</li>
                                            <li style="margin-bottom: 10px;">Use a stable connection with camera + microphone permissions</li>
                                            <li style="margin-bottom: 10px;">Choose a quiet, well-lit space for best results</li>
                                            <li>Estimated duration: 30–45 minutes</li>
                                        </ul>
                                    </div>
                                    
                                    <p style="margin: 24px 0 0; color: rgba(255, 255, 255, 0.55); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        Need help? Reply to your recruiter or reach us at support@skillscreen.io.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 24px 32px 32px; background: rgba(255, 255, 255, 0.02); border-top: 1px solid rgba(255, 255, 255, 0.08);">
                                    <p style="margin: 0; color: rgba(255, 255, 255, 0.5); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        © 2025 SkillScreen. Intelligent hiring infrastructure.
                                    </p>
                                    <p style="margin: 6px 0 0; color: rgba(255, 255, 255, 0.4); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        This inbox is unattended. Replies are not monitored.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    def _build_completion_email_html(
        self,
        recruiter_name: str,
        candidate_name: str,
        summary_link: str,
        interview_id: str
    ) -> str:
        """Build HTML content for interview completion notification"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interview Completed</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #050505; color: #ffffff;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #050505;">
                <tr>
                    <td align="center" style="padding: 48px 20px;">
                        <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 32px 32px 0; text-align: left;">
                                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.2em; color: rgba(255, 255, 255, 0.55); margin-bottom: 12px;">
                                        SkillScreen
                                    </div>
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: -0.03em;">
                                        Interview Completed
                                    </h1>
                                    <p style="margin: 8px 0 0; color: rgba(255, 255, 255, 0.65); font-size: 14px;">
                                        Candidate results are ready
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 32px;">
                                    <p style="margin: 0 0 24px; color: #ffffff; font-size: 17px; line-height: 1.6; font-weight: 400;">
                                        Hello <strong style="font-weight: 600;">{recruiter_name}</strong>,
                                    </p>
                                    
                                    <div style="margin: 0 0 24px; padding: 20px 24px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;">
                                        <p style="margin: 0; color: rgba(255, 255, 255, 0.82); font-size: 15px; line-height: 1.7;">
                                            <strong style="font-weight: 600; color: #ffffff;">{candidate_name}</strong> completed their interview. Transcripts, AI notes, and action items are ready for review.
                                        </p>
                                    </div>
                                    
                                    <p style="margin: 0 0 32px; color: rgba(255, 255, 255, 0.7); font-size: 14px; line-height: 1.6; font-weight: 400;">
                                        Open the summary dashboard to access insights, playback, and recommendations.
                                    </p>
                                    
                                    <!-- CTA Button -->
                                    <table role="presentation" style="margin: 0 0 32px;">
                                        <tr>
                                            <td>
                                                <a href="{summary_link}" 
                                                   style="display: inline-block; padding: 14px 28px; background-color: #ffffff; color: #050505; text-decoration: none; font-size: 14px; font-weight: 600; border-radius: 999px; letter-spacing: 0.01em;">
                                                    View Interview Summary
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Interview Details -->
                                    <div style="margin: 32px 0; padding: 24px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;">
                                        <h3 style="margin: 0 0 16px; color: #ffffff; font-size: 14px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;">
                                            Interview Details
                                        </h3>
                                        <table style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 10px 0; color: rgba(255, 255, 255, 0.65); font-size: 13px; font-weight: 400;">Candidate</td>
                                                <td style="padding: 10px 0; color: #ffffff; font-size: 13px; font-weight: 600; text-align: right;">{candidate_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 10px 0; color: rgba(255, 255, 255, 0.65); font-size: 13px; font-weight: 400;">Interview ID</td>
                                                <td style="padding: 10px 0; color: #ffffff; font-size: 13px; font-weight: 600; text-align: right;">{interview_id}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 10px 0; color: rgba(255, 255, 255, 0.65); font-size: 13px; font-weight: 400;">Completed</td>
                                                <td style="padding: 10px 0; color: #ffffff; font-size: 13px; font-weight: 600; text-align: right;">{datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <p style="margin: 24px 0 0; color: rgba(255, 255, 255, 0.55); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        The AI analysis is still processing. We'll notify you when additional insights are appended to the summary.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 24px 32px 32px; background: rgba(255, 255, 255, 0.02); border-top: 1px solid rgba(255, 255, 255, 0.08);">
                                    <p style="margin: 0; color: rgba(255, 255, 255, 0.5); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        © 2025 SkillScreen. Intelligent hiring infrastructure.
                                    </p>
                                    <p style="margin: 6px 0 0; color: rgba(255, 255, 255, 0.4); font-size: 12px; line-height: 1.6; font-weight: 400;">
                                        This inbox is unattended. Replies are not monitored.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """


# Create a singleton instance WITHOUT token_store (will be injected from interview.py)
# This allows interview.py to pass the token_store reference
email_service = EmailService()

