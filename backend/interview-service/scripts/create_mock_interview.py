"""
Script to create a mock interview record for Dimantha Goonewardena
"""
import sys
import os
from datetime import datetime, timezone
import uuid

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common-service'))

from db import DBFactory
from repository.interview_repository import InterviewRepository
from repository.candidate_repository import CandidateRepository

def create_mock_interview():
    """Create a mock interview for Dimantha Goonewardena"""
    
    # Initialize database
    DBFactory.init()
    session = DBFactory.get_session()
    
    try:
        # Find Dimantha Goonewardena's candidate record
        candidate_repo = CandidateRepository(session)
        
        # Search for candidate by email
        hardcoded_org_id = "e5d2d50b-6c07-43cd-8a78-ffd7b5b377bb"
        candidate = candidate_repo.get_candidate_by_email(
            hardcoded_org_id,
            "goonewardenadimantha@gmail.com"
        )
        
        if not candidate:
            print("❌ Candidate not found. Please upload the resume first.")
            return None
        
        candidate_id = str(candidate.id)
        print(f"✅ Found candidate: {candidate.full_name} (ID: {candidate_id})")
        
        # Check if interview already exists
        interview_repo = InterviewRepository(session)
        existing_interviews = interview_repo.get_interviews_by_candidate(candidate_id)
        
        if existing_interviews:
            print(f"⚠️  Interview already exists for this candidate: {existing_interviews[0].id}")
            return str(existing_interviews[0].id)
        
        # Generate session_id
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = f"session_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Use mock IDs from sample data
        mock_job_position_id = "4398af02-6307-4ae9-a946-da03cd10bb78"
        mock_template_id = "1ef03eb1-4ba0-4e42-a27d-5b5a868640f4"
        
        # Create interview record matching the sample format
        interview_data = {
            'organization_id': hardcoded_org_id,
            'job_position_id': mock_job_position_id,  # Required field
            'candidate_id': candidate_id,
            'template_id': mock_template_id,  # Required field
            'status': 'completed',  # Set as completed so it shows up with full data
            'mode': 'chat',
            'scheduled_at': datetime.now(timezone.utc).isoformat(),
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'settings': {
                'difficulty': 'medium',
                'session_id': session_id,
                'max_questions': 15,
                'interview_type': 'mixed',
                'candidate_record_id': candidate_id,
                'target_duration_minutes': 12
            }
        }
        
        interview = interview_repo.create_interview(interview_data)
        session.commit()
        
        interview_id = str(interview.id)
        print(f"✅ Created mock interview: {interview_id}")
        print(f"   Candidate: {candidate.full_name}")
        print(f"   Status: {interview.status}")
        print(f"   Session ID: {session_id}")
        
        return interview_id
        
    except Exception as e:
        print(f"❌ Error creating mock interview: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return None
    finally:
        session.close()

if __name__ == "__main__":
    interview_id = create_mock_interview()
    if interview_id:
        print(f"\n🎉 Mock interview created successfully!")
        print(f"   Interview ID: {interview_id}")
        print(f"   View at: http://localhost:3000/interview-summary?id={interview_id}")

