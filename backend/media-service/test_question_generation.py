import requests
import json
import os
from sqlalchemy import create_engine, text

# Database connection
DB_URL = "postgresql://intervuai:LOYALlist_2025@skillscreen-postgres.postgres.database.azure.com:5432/skillscreen_database?sslmode=require"
ORCHESTRATION_URL = "http://localhost:8004"  # Assuming orchestration service runs on 8004 locally or via port forward

def get_latest_interview_id():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM interviews ORDER BY created_at DESC LIMIT 1"))
            row = result.fetchone()
            if row:
                return str(row[0])
    except Exception as e:
        print(f"Error fetching interview ID: {e}")
    return None

def test_next_question(interview_id, response_text, question_number):
    url = f"{ORCHESTRATION_URL}/interviews/{interview_id}/next-question"
    payload = {
        "previous_response": response_text,
        "question_number": question_number
    }
    
    print(f"\n--- Testing Question {question_number} ---")
    print(f"Input Response: {response_text}")
    
    try:
        # We need to run this inside the container or port forward. 
        # Since I am running this script from the host, I need to know the exposed port.
        # Let's assume I'll run this script INSIDE the orchestration-service container for easier access to internal URLs if needed,
        # OR I can use the gateway if exposed. 
        # But for now, let's try to run it from host and assume I can hit the service.
        # If not, I'll run it via docker exec.
        pass
    except Exception as e:
        pass

if __name__ == "__main__":
    print("Fetching latest interview ID...")
    interview_id = get_latest_interview_id()
    
    if not interview_id:
        print("No interview found in DB.")
        exit(1)
        
    print(f"Using Interview ID: {interview_id}")
    
    # Test 1: Generic response
    # We will print the curl command to run, as running requests from here might be tricky with network
    print("\nRun the following command to test:")
    print(f"curl -X POST http://localhost:8000/orchestration/interviews/{interview_id}/next-question \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"previous_response\": \"I have 5 years of experience in Python and building scalable backend systems.\", \"question_number\": 1}}'")

    # Test 2: Different response to check dynamic generation
    print("\nRun this to check dynamic generation (different response):")
    print(f"curl -X POST http://localhost:8000/orchestration/interviews/{interview_id}/next-question \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"previous_response\": \"I specialize in frontend development with React and Next.js.\", \"question_number\": 1}}'")
