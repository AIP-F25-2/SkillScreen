"""
Insert complete dummy data into the database for testing
This includes all tables with proper foreign key relationships
"""

import sys
import os
from datetime import datetime, timezone
import uuid

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import db_manager
from database.models import (
    Organization, User, Candidate, JobPosition, InterviewTemplate,
    Interview, InterviewSession, Response, AIAnalysis, UserRole,
    InterviewStatus, InterviewMode
)
from services.database_service import InterviewDataService
from sqlalchemy.orm import Session

print("="*60)
print("Inserting Complete Dummy Data into Database")
print("="*60)

db: Session = db_manager.get_session_sync()

try:
    # 1. Get or create default organization
    print("\n1. Creating/Getting organization...")
    org = db.query(Organization).filter(Organization.name == "Test Organization").first()
    if not org:
        org = Organization(
            name="Test Organization",
            domain="test.com",
            settings={}
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    print(f"   [OK] Organization ID: {org.id}")
    
    # 2. Create dummy users (for foreign key constraints)
    print("\n2. Creating users...")
    db_service = InterviewDataService(db)
    user_ids = []  # Store IDs instead of User objects to avoid enum issues
    user_data = [
        {"email": "john.doe@test.com", "first": "John", "last": "Doe", "role": UserRole.CANDIDATE},
        {"email": "jane.smith@test.com", "first": "Jane", "last": "Smith", "role": UserRole.CANDIDATE},
        {"email": "bob.johnson@test.com", "first": "Bob", "last": "Johnson", "role": UserRole.CANDIDATE},
        {"email": "alice.williams@test.com", "first": "Alice", "last": "Williams", "role": UserRole.CANDIDATE},
        {"email": "charlie.brown@test.com", "first": "Charlie", "last": "Brown", "role": UserRole.CANDIDATE}
    ]
    
    for data in user_data:
        # Query using raw SQL to avoid enum conversion issues
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id, email FROM users WHERE email = :email"),
            {"email": data["email"]}
        ).first()
        
        if result:
            user_id = result[0]  # UUID from database
            user_email = result[1]
            print(f"   [OK] User exists: {user_email} ({user_id})")
        else:
            # Create new user using database service
            user = db_service.create_user(
                organization_id=str(org.id),
                email=data["email"],
                first_name=data["first"],
                last_name=data["last"],
                role=data["role"]
            )
            user_id = user.id  # UUID from created user
            print(f"   [OK] User created: {data['email']} ({user_id})")
        
        # Ensure user_id is a UUID object
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        user_ids.append(user_id)
    
    # 3. Create dummy candidates
    print("\n3. Creating candidates...")
    candidates = []
    candidate_data = [
        {"name": "John Doe", "email": "john.doe@test.com", "skills": ["Python", "FastAPI", "PostgreSQL"]},
        {"name": "Jane Smith", "email": "jane.smith@test.com", "skills": ["JavaScript", "React", "Node.js"]},
        {"name": "Bob Johnson", "email": "bob.johnson@test.com", "skills": ["Java", "Spring", "MySQL"]},
        {"name": "Alice Williams", "email": "alice.williams@test.com", "skills": ["Python", "Django", "MongoDB"]},
        {"name": "Charlie Brown", "email": "charlie.brown@test.com", "skills": ["C++", "Linux", "Docker"]}
    ]
    
    for i, data in enumerate(candidate_data):
        candidate = db.query(Candidate).filter(Candidate.email == data["email"]).first()
        if not candidate:
            candidate = Candidate(
                organization_id=org.id,
                full_name=data["name"],
                email=data["email"],
                skills=data["skills"]
            )
            db.add(candidate)
        candidates.append(candidate)
    
    db.commit()
    for candidate in candidates:
        db.refresh(candidate)
        print(f"   [OK] Candidate: {candidate.full_name} ({candidate.id})")
    
    # 4. Create dummy jobs
    print("\n4. Creating job positions...")
    jobs = []
    job_data = [
        {"title": "Senior Python Developer", "skills": ["Python", "FastAPI", "PostgreSQL"]},
        {"title": "Full Stack Developer", "skills": ["JavaScript", "React", "Node.js"]},
        {"title": "Backend Engineer", "skills": ["Java", "Spring", "MySQL"]},
        {"title": "Python Developer", "skills": ["Python", "Django", "MongoDB"]},
        {"title": "Systems Engineer", "skills": ["C++", "Linux", "Docker"]}
    ]
    
    for data in job_data:
        job = JobPosition(
            organization_id=org.id,
            title=data["title"],
            description=f"Position for {data['title']}",
            required_skills=data["skills"],
            is_active=True
        )
        db.add(job)
        jobs.append(job)
    
    db.commit()
    for job in jobs:
        db.refresh(job)
        print(f"   [OK] Job: {job.title} ({job.id})")
    
    # 5. Create interview template
    print("\n5. Creating interview template...")
    template = db.query(InterviewTemplate).filter(
        InterviewTemplate.organization_id == org.id,
        InterviewTemplate.name == "Default Template"
    ).first()
    
    if not template:
        template = InterviewTemplate(
            organization_id=org.id,
            name="Default Template",
            type="technical",
            questions=[],
            settings={}
        )
        db.add(template)
        db.commit()
        db.refresh(template)
    print(f"   [OK] Template ID: {template.id}")
    
    # 6. Create dummy interviews with proper foreign keys
    print("\n6. Creating interviews...")
    interviews = []
    
    for i in range(5):
        user_id = user_ids[i]  # Use stored user ID
        candidate = candidates[i]
        job = jobs[i]
        
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        interview_id = uuid.uuid4()
        
        # Use raw SQL to insert with correct enum values (lowercase)
        from sqlalchemy import text
        import json
        settings_json = json.dumps({
            "session_id": session_id,
            "candidate_record_id": str(candidate.id),
            "interview_type": "technical",
            "max_questions": 5
        })
        
        db.execute(
            text("""
                INSERT INTO interviews (id, organization_id, job_position_id, candidate_id, 
                    template_id, status, mode, started_at, settings)
                VALUES (:id, :org_id, :job_id, :candidate_id, :template_id, 
                    'in_progress'::interview_status, 'chat'::interview_mode, :started_at, CAST(:settings AS jsonb))
            """),
            {
                "id": interview_id,
                "org_id": org.id,
                "job_id": job.id,
                "candidate_id": candidate.id,
                "template_id": template.id,
                "started_at": datetime.now(timezone.utc),
                "settings": settings_json
            }
        )
        db.commit()
        
        # Create Interview object for later use
        interview = Interview()
        interview.id = interview_id
        interview.organization_id = org.id
        interview.job_position_id = job.id
        interview.candidate_id = candidate.id
        interview.template_id = template.id
        interview.status = InterviewStatus.IN_PROGRESS.value
        interview.mode = InterviewMode.CHAT.value
        interview.started_at = datetime.now(timezone.utc)
        interview.settings = json.loads(settings_json)
        interviews.append(interview)
        
        print(f"   [OK] Interview: {interview_id} (session: {session_id})")
    
    # 7. Create interview sessions
    print("\n7. Creating interview sessions...")
    sessions = []
    
    for i, interview in enumerate(interviews):
        job = jobs[i]
        question_text = f"Tell me about your experience with {job.required_skills[0] if job.required_skills else 'programming'}."
        response_text = f"I have {i+2} years of experience working with {', '.join(job.required_skills[:2])}. I've worked on several projects involving these technologies."
        
        session_id = uuid.uuid4()
        
        # Use raw SQL to avoid model/database mismatch
        db.execute(
            text("""
                INSERT INTO interview_sessions (id, interview_id, question_id, question_text, 
                    question_type, candidate_response, response_duration, started_at, completed_at)
                VALUES (:id, :interview_id, :question_id, :question_text, :question_type, 
                    :candidate_response, :response_duration, :started_at, :completed_at)
            """),
            {
                "id": session_id,
                "interview_id": interview.id,
                "question_id": str(uuid.uuid4()),
                "question_text": question_text,
                "question_type": "technical",
                "candidate_response": response_text,
                "response_duration": 45 + i * 10,
                "started_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            }
        )
        db.commit()
        
        # Create session object for later use
        session = InterviewSession()
        session.id = session_id
        session.interview_id = interview.id
        session.question_text = question_text
        session.candidate_response = response_text
        sessions.append(session)
        
        print(f"   [OK] Session: {session_id}")
    
    # 8. Create responses
    print("\n8. Creating responses...")
    responses = []
    
    for i, session in enumerate(sessions):
        interview = interviews[i]
        user_id = user_ids[i]  # Use User ID for responder_id
        response_text = session.candidate_response
        
        response = Response(
            interview_id=interview.id,
            session_id=session.id,
            responder_id=user_id,  # responder_id references users.id
            response_text=response_text,
            duration_ms=(45 + i * 10) * 1000,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(response)
        responses.append(response)
    
    db.commit()
    for response in responses:
        db.refresh(response)
        print(f"   [OK] Response: {response.id}")
    
    # 9. Create AI analyses
    print("\n9. Creating AI analyses...")
    ai_analyses = []
    
    for i, (session, response) in enumerate(zip(sessions, responses)):
        interview = interviews[i]
        candidate = candidates[i]
        job = jobs[i]
        
        # For individual responses, store response-level analysis
        analysis_data = {
            'response_analysis': {
                'behavioral_analysis': {
                    'behavior_type': ['engaged', 'consistent', 'declining', 'erratic', 'engaged'][i],
                    'anomaly_score': 0.1 + i * 0.05,
                    'engagement_trend': ['increasing', 'stable', 'decreasing', 'stable', 'increasing'][i],
                    'consistency_score': 0.7 + i * 0.05,
                    'behavioral_flags': [],
                    'engagement_score': 0.6 + i * 0.08
                },
                'quality_prediction': {
                    'predicted_score': 6.5 + i * 0.5,
                    'confidence': 0.75 + i * 0.05,
                    'feature_importance': {
                        'response_length': 0.2,
                        'vocabulary_diversity': 0.15,
                        'technical_keywords': 0.25
                    },
                    'model_used': 'ensemble'
                },
                'bias_detection': None
            },
            'metadata': {
                'question_number': 1,
                'response_length': len(response.response_text),
                'response_time_seconds': 45 + i * 10,
                'candidate_name': candidate.full_name,
                'job_title': job.title,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Confidence score should be between 1-10, not 0-1
        confidence_score = 6.5 + i * 0.5  # Range: 6.5 to 9.0
        
        ai_analysis = AIAnalysis(
            interview_id=interview.id,
            session_id=session.id,
            analysis_type="text_analysis",
            service_name="text-service",
            raw_results=analysis_data,
            confidence_score=confidence_score,
            processing_time=150 + i * 20,
            version="v1.0"
        )
        db.add(ai_analysis)
        ai_analyses.append(ai_analysis)
    
    db.commit()
    for ai_analysis in ai_analyses:
        db.refresh(ai_analysis)
        print(f"   [OK] AI Analysis: {ai_analysis.id} (confidence: {ai_analysis.confidence_score:.2f})")
    
    # 10. Create final interview summary analysis (simulating completed interview)
    print("\n10. Creating interview summary analyses...")
    summary_analyses = []
    
    for i, interview in enumerate(interviews):
        candidate = candidates[i]
        job = jobs[i]
        
        # Simulate the summary data that would be returned by the API
        summary_data = {
            'executive_summary': f"Interview completed for {candidate.full_name} applying for {job.title}. Overall performance was {'strong' if i < 3 else 'moderate'}.",
            'overall_score': round(6.5 + i * 0.5, 1),
            'recommendation': ['Hire', 'Strong Consider', 'Consider', 'Weak Consider', 'Reject'][i],
            'recommendation_reason': f"Based on {i+2} responses with {'consistent' if i % 2 == 0 else 'variable'} performance.",
            'technical_assessment': {
                'score': 6.0 + i * 0.4,
                'summary': f"Demonstrated {'strong' if i < 2 else 'adequate'} technical knowledge in {', '.join(job.required_skills[:2])}."
            },
            'communication_assessment': {
                'score': 7.0 + i * 0.3,
                'summary': f"Communication skills were {'excellent' if i < 2 else 'good'} with clear articulation."
            },
            'cultural_fit': {
                'score': 6.5 + i * 0.35,
                'summary': f"Cultural alignment appears {'strong' if i < 3 else 'moderate'}."
            },
            'strengths': [
                f"Strong experience with {job.required_skills[0] if job.required_skills else 'relevant technologies'}",
                f"{i+2} years of professional experience",
                "Clear communication style"
            ],
            'areas_for_improvement': [
                "Could provide more specific examples",
                "Consider elaborating on technical details"
            ],
            'key_highlights': [
                f"Completed interview with {i+2} responses",
                f"Demonstrated knowledge in {', '.join(job.required_skills[:2]) if job.required_skills else 'relevant areas'}"
            ],
            'red_flags': [],
            'improvement_tips': [
                "Continue building technical depth",
                "Practice articulating complex concepts"
            ],
            'next_steps': [
                "Schedule follow-up interview" if i < 2 else "Review with hiring team",
                "Check references"
            ],
            'interviewer_notes': f"Overall impression: {'Positive' if i < 3 else 'Neutral'}. Candidate showed {'strong' if i < 2 else 'adequate'} potential."
        }
        
        # Store summary in ai_analysis
        summary_raw_results = {
            'interview_summary': summary_data,  # Full summary data (whatever API returns)
            'summary_type': 'final_assessment',
            'metadata': {
                'interview_id': str(interview.id),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_version': 'v1.0'
            }
        }
        
        summary_confidence = summary_data['overall_score']
        
        summary_analysis = AIAnalysis(
            interview_id=interview.id,
            session_id=None,  # Summary is interview-level
            analysis_type='interview_summary',
            service_name='text-service',
            raw_results=summary_raw_results,
            confidence_score=summary_confidence,
            processing_time=200 + i * 30,
            version='v1.0'
        )
        db.add(summary_analysis)
        summary_analyses.append(summary_analysis)
    
    db.commit()
    for summary_analysis in summary_analyses:
        db.refresh(summary_analysis)
        print(f"   [OK] Summary Analysis: {summary_analysis.id} (confidence: {summary_analysis.confidence_score:.2f})")
    
    print("\n" + "="*60)
    print("[SUCCESS] Inserted complete dummy data!")
    print("="*60)
    print("\nSummary:")
    print(f"  - Organization: 1")
    print(f"  - Users: {len(user_ids)}")
    print(f"  - Candidates: {len(candidates)}")
    print(f"  - Jobs: {len(jobs)}")
    print(f"  - Interviews: {len(interviews)}")
    print(f"  - Interview Sessions: {len(sessions)}")
    print(f"  - Responses: {len(responses)}")
    print(f"  - AI Analyses (response-level): {len(ai_analyses)}")
    print(f"  - AI Analyses (summary-level): {len(summary_analyses)}")
    print("\nAll data inserted with proper foreign key relationships!")
    print("\nNote: Summary analyses contain the full interview summary data")
    print("      that would be returned by the API (executive_summary, overall_score,")
    print("      recommendation, assessments, strengths, etc.)")
    print("\nYou can now test the interview flow with existing data.")
    print("\nTo verify data:")
    print("  SELECT COUNT(*) FROM interviews;")
    print("  SELECT COUNT(*) FROM interview_sessions;")
    print("  SELECT COUNT(*) FROM responses;")
    print("  SELECT COUNT(*) FROM ai_analysis WHERE analysis_type = 'text_analysis';")
    print("  SELECT COUNT(*) FROM ai_analysis WHERE analysis_type = 'interview_summary';")
    
except Exception as e:
    print(f"\n[ERROR] Failed to insert dummy data: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

