"""
Email service for sending interview invitations using Resend
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv("RESEND_API_KEY", "")

class EmailService:
    """Service for sending interview invitation emails"""
    
    def __init__(self):
        self.from_email = os.getenv("FROM_EMAIL", "interviews@skillscreen.io")
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
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
            subject = f"Your Interview Invitation - {company_name or 'SkillScreen'}"
            
            html_content = self._build_invitation_email_html(
                candidate_name=candidate_name,
                interview_link=interview_link,
                recruiter_name=recruiter_name,
                company_name=company_name,
                expires_at=expires_at
            )
            
            # Send email via Resend
            response = resend.Emails.send({
                "from": self.from_email,
                "to": candidate_email,
                "subject": subject,
                "html": html_content,
            })
            
            logger.info(f"Interview invitation sent to {candidate_email} (session: {session_id})")
            
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
        expires_at: datetime
    ) -> str:
        """Build HTML content for interview invitation email"""
        
        recruiter_text = f"{recruiter_name} from " if recruiter_name else ""
        company_text = company_name or "SkillScreen"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interview Invitation</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                        Interview Invitation
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                        Hello <strong>{candidate_name}</strong>,
                                    </p>
                                    
                                    <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                        {recruiter_text}<strong>{company_text}</strong> has invited you to complete an AI-powered interview.
                                    </p>
                                    
                                    <p style="margin: 0 0 30px; color: #666666; font-size: 14px; line-height: 1.6;">
                                        This is a secure, one-time link that will guide you through the interview process. 
                                        Please click the button below to begin:
                                    </p>
                                    
                                    <!-- CTA Button -->
                                    <table role="presentation" style="margin: 0 auto;">
                                        <tr>
                                            <td style="border-radius: 6px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                                                <a href="{interview_link}" 
                                                   style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: bold;">
                                                    Start Your Interview
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Important Info -->
                                    <div style="margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px;">
                                        <h3 style="margin: 0 0 10px; color: #333333; font-size: 16px;">
                                            Important Information:
                                        </h3>
                                        <ul style="margin: 0; padding-left: 20px; color: #666666; font-size: 14px; line-height: 1.8;">
                                            <li>This link expires on <strong>{expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}</strong></li>
                                            <li>This is a one-time use link - please do not refresh the page during the interview</li>
                                            <li>Ensure you have a working camera and microphone</li>
                                            <li>Find a quiet, well-lit location for the interview</li>
                                            <li>The interview typically takes 30-45 minutes</li>
                                        </ul>
                                    </div>
                                    
                                    <p style="margin: 20px 0 0; color: #999999; font-size: 12px; line-height: 1.6;">
                                        If you have any questions or issues accessing the interview, please contact your recruiter.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px 40px; text-align: center; background-color: #f8f9fa; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; color: #999999; font-size: 12px;">
                                        © 2025 SkillScreen. All rights reserved.
                                    </p>
                                    <p style="margin: 10px 0 0; color: #999999; font-size: 12px;">
                                        This is an automated email. Please do not reply.
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
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                        ✓ Interview Completed
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                        Hello <strong>{recruiter_name}</strong>,
                                    </p>
                                    
                                    <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                        <strong>{candidate_name}</strong> has successfully completed their interview.
                                    </p>
                                    
                                    <p style="margin: 0 0 30px; color: #666666; font-size: 14px; line-height: 1.6;">
                                        The interview has been recorded and transcribed. Click below to view the complete summary and transcript:
                                    </p>
                                    
                                    <!-- CTA Button -->
                                    <table role="presentation" style="margin: 0 auto;">
                                        <tr>
                                            <td style="border-radius: 6px; background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                                                <a href="{summary_link}" 
                                                   style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: bold;">
                                                    View Interview Summary
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Interview Details -->
                                    <div style="margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-radius: 4px;">
                                        <h3 style="margin: 0 0 10px; color: #333333; font-size: 16px;">
                                            Interview Details:
                                        </h3>
                                        <table style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 8px 0; color: #666666; font-size: 14px;">Candidate:</td>
                                                <td style="padding: 8px 0; color: #333333; font-size: 14px; font-weight: bold; text-align: right;">{candidate_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #666666; font-size: 14px;">Interview ID:</td>
                                                <td style="padding: 8px 0; color: #333333; font-size: 14px; font-weight: bold; text-align: right;">{interview_id}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #666666; font-size: 14px;">Completed:</td>
                                                <td style="padding: 8px 0; color: #333333; font-size: 14px; font-weight: bold; text-align: right;">{datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <p style="margin: 20px 0 0; color: #999999; font-size: 12px; line-height: 1.6;">
                                        The AI analysis and transcript are being generated and will be available shortly in the summary.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px 40px; text-align: center; background-color: #f8f9fa; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; color: #999999; font-size: 12px;">
                                        © 2025 SkillScreen. All rights reserved.
                                    </p>
                                    <p style="margin: 10px 0 0; color: #999999; font-size: 12px;">
                                        This is an automated notification. Please do not reply.
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


# Create a singleton instance
email_service = EmailService()

