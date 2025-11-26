"""
Script to create a mock interview entry in media_files table with transcript and analysis
"""
import sys
import os
from datetime import datetime, timezone
import uuid

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db import UnitOfWork
from app.db.schema import media as media_table
from sqlalchemy import select

# Mock transcript data
MOCK_TRANSCRIPT = {
    "messages": [
        {
            "role": "system",
            "content": "Interview started for Dimantha Goonewardena"
        },
        {
            "role": "interviewer",
            "content": "Hello Dimantha! Thank you for joining us today. Let's start with a brief introduction. Can you tell me about yourself and your background in software development?"
        },
        {
            "role": "candidate",
            "content": "Hi! I'm Dimantha Goonewardena, and I'm currently pursuing a Post Graduate Diploma in Computer Software and Database Development at Loyalist College in Toronto. I have experience as a Software Developer Intern at Raytronics Computer Systems in Sri Lanka, where I worked on various web applications using React, Node.js, and MongoDB."
        },
        {
            "role": "interviewer",
            "content": "That's great! Can you walk me through a challenging project you've worked on and how you approached solving it?"
        },
        {
            "role": "candidate",
            "content": "One of the most challenging projects was building a real-time chat application. I had to implement WebSocket connections for real-time messaging, handle concurrent users, and ensure data consistency. I used React for the frontend, Node.js with Socket.io for the backend, and MongoDB for storage. The main challenge was managing state across multiple components and handling reconnection logic."
        },
        {
            "role": "interviewer",
            "content": "Excellent! How do you handle debugging and troubleshooting in your development process?"
        },
        {
            "role": "candidate",
            "content": "I follow a systematic approach: first, I reproduce the issue consistently, then I use browser DevTools and console logs to trace the problem. For backend issues, I check server logs and use debugging tools. I also write unit tests to catch issues early. When stuck, I search documentation and Stack Overflow, and I'm not afraid to ask for help from my team."
        },
        {
            "role": "interviewer",
            "content": "What are your thoughts on code quality and best practices?"
        },
        {
            "role": "candidate",
            "content": "I believe clean, readable code is crucial. I follow SOLID principles, write meaningful variable names, add comments where necessary, and ensure proper error handling. I also practice code reviews with my peers and use linters like ESLint to maintain consistency. Version control with Git is essential for tracking changes and collaboration."
        },
        {
            "role": "interviewer",
            "content": "Thank you, Dimantha! That concludes our interview. We'll be in touch soon."
        }
    ],
    "duration_seconds": 720,
    "word_count": 450
}

# Mock analysis data
MOCK_ANALYSIS = {
    "overall_score": 88,
    "categories": [
        {
            "name": "Technical Proficiency",
            "score": 90,
            "feedback": "Strong understanding of React, Node.js, and modern web development. Demonstrates solid knowledge of real-time systems and database design."
        },
        {
            "name": "Communication",
            "score": 85,
            "feedback": "Clear and articulate explanations. Provides concrete examples and demonstrates good listening skills."
        },
        {
            "name": "Problem Solving",
            "score": 87,
            "feedback": "Shows systematic approach to debugging and troubleshooting. Good analytical thinking and resourcefulness."
        },
        {
            "name": "Cultural Fit",
            "score": 90,
            "feedback": "Values code quality and collaboration. Open to learning and asking for help when needed."
        }
    ],
    "key_strengths": [
        "Strong technical foundation in full-stack development",
        "Experience with real-time systems and WebSocket implementations",
        "Good understanding of debugging and troubleshooting processes",
        "Commitment to code quality and best practices",
        "Collaborative approach and willingness to learn"
    ],
    "areas_for_improvement": [
        "Could provide more specific metrics or results from past projects",
        "Might benefit from more experience with large-scale systems",
        "Could expand knowledge of cloud services and DevOps practices"
    ],
    "sentiment_analysis": {
        "overall": "positive",
        "confidence": 0.92,
        "keywords": ["enthusiastic", "confident", "collaborative", "professional"]
    }
}

def create_mock_interview_media():
    """Create a mock interview entry in media_files table"""
    
    # Use the interview ID from the interview we just created
    interview_id = "42413923-9840-4893-9524-24adab502886"
    
    with UnitOfWork() as uow:
        # Check if entry already exists
        existing = uow.session.execute(
            select(media_table)
            .where(media_table.c.file_type == "interview",
                   media_table.c.interview_id == interview_id)
        ).mappings().one_or_none()
        
        if existing:
            print(f"⚠️  Interview media entry already exists for interview {interview_id}")
            return interview_id
        
        # Create metadata with transcript and analysis
        metadata = {
            "transcript": MOCK_TRANSCRIPT,
            "analysis": MOCK_ANALYSIS,
            "status": "completed",
            "candidate_name": "Dimantha Goonewardena",
            "candidate_email": "goonewardenadimantha@gmail.com",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into media_files table
        result = uow.session.execute(
            media_table.insert().values(
                interview_id=interview_id,
                file_type="interview",
                status="completed",
                metadata=metadata,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ).returning(media_table)
        )
        
        row = result.mappings().one()
        # UnitOfWork auto-commits on exit
        
        print(f"✅ Created mock interview media entry")
        print(f"   Interview ID: {interview_id}")
        print(f"   Media ID: {row['id']}")
        print(f"   Status: {row['status']}")
        
        return interview_id

if __name__ == "__main__":
    interview_id = create_mock_interview_media()
    if interview_id:
        print(f"\n🎉 Mock interview media created successfully!")
        print(f"   View at: http://localhost:3000/interview-summary?id={interview_id}")

