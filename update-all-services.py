#!/usr/bin/env python3
"""
Script to add standardized /api endpoints to all services
"""

import os
import sys

# Service configurations
services = [
    {
        "name": "interview-service",
        "port": 5003,
        "description": "Interview management and scheduling",
        "data_query": "SELECT id, title, status, created_at FROM interviews",
        "table_name": "interviews"
    },
    {
        "name": "media-service", 
        "port": 5004,
        "description": "File upload and media management",
        "data_query": "SELECT id, filename, file_type, size, created_at FROM media_files",
        "table_name": "media_files"
    },
    {
        "name": "video-ai-service",
        "port": 5005,
        "description": "Video analysis and AI processing",
        "data_query": "SELECT id, video_url, analysis_status, created_at FROM video_analyses",
        "table_name": "video_analyses"
    },
    {
        "name": "audio-ai-service",
        "port": 5006,
        "description": "Audio analysis and transcription",
        "data_query": "SELECT id, audio_url, transcription_status, created_at FROM audio_analyses", 
        "table_name": "audio_analyses"
    },
    {
        "name": "text-ai-service",
        "port": 5007,
        "description": "Text analysis and NLP processing",
        "data_query": "SELECT id, text_content, analysis_type, created_at FROM text_analyses",
        "table_name": "text_analyses"
    },
    {
        "name": "assessment-service",
        "port": 5008,
        "description": "Assessment creation and scoring",
        "data_query": "SELECT id, title, assessment_type, created_at FROM assessments",
        "table_name": "assessments"
    },
    {
        "name": "coding-service",
        "port": 5009,
        "description": "Code execution and validation",
        "data_query": "SELECT id, code_snippet, language, execution_status, created_at FROM code_submissions",
        "table_name": "code_submissions"
    },
    {
        "name": "logger-service",
        "port": 5010,
        "description": "Centralized logging and monitoring",
        "data_query": "SELECT id, level, service, message, created_at FROM logs",
        "table_name": "logs"
    },
    {
        "name": "notification-service",
        "port": 5011,
        "description": "Email and SMS notifications",
        "data_query": "SELECT id, recipient, notification_type, status, created_at FROM notifications",
        "table_name": "notifications"
    }
]

def create_api_endpoint_code(service):
    """Generate the API endpoint code for a service"""
    return f'''@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Get {service['table_name']} data
        {service['table_name']} = db.execute_query("{service['data_query']}")
        {service['table_name']}_data = [dict(item) for item in {service['table_name']}]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len({service['table_name']}_data)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({{
            "success": True,
            "data": {service['table_name']}_data,
            "meta": {{
                "pagination": {{
                    "current_page": current_page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_count": total_count
                }},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": f"req_{{str(uuid.uuid4())[:8]}}"
            }}
        }})
    except Exception as e:
        logger.error(f"Failed to get API data: {{str(e)}}")
        return jsonify({{
            "success": False,
            "data": [],
            "meta": {{
                "pagination": {{
                    "current_page": 1,
                    "per_page": 20,
                    "total_pages": 0,
                    "total_count": 0
                }},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": f"req_{{str(uuid.uuid4())[:8]}}",
                "error": str(e)
            }}
        }}), 500'''

def update_service_file(service):
    """Update a service file with the API endpoint"""
    file_path = f"backend/{service['name']}/app.py"
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} does not exist, skipping...")
        return False
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if /api endpoint already exists
    if '/api' in content:
        print(f"API endpoint already exists in {file_path}, skipping...")
        return True
    
    # Find the position to insert the new endpoint (after /info endpoint)
    info_endpoint_pos = content.find('@app.route(\'/info\'')
    if info_endpoint_pos == -1:
        print(f"Warning: Could not find /info endpoint in {file_path}, skipping...")
        return False
    
    # Find the end of the /info function
    lines = content.split('\n')
    insert_line = -1
    brace_count = 0
    in_info_function = False
    
    for i, line in enumerate(lines):
        if '@app.route(\'/info\'' in line:
            in_info_function = True
        if in_info_function:
            brace_count += line.count('}')
            if brace_count > 0 and line.strip() == '}':
                insert_line = i + 1
                break
    
    if insert_line == -1:
        print(f"Warning: Could not find end of /info function in {file_path}, skipping...")
        return False
    
    # Generate the API endpoint code
    api_code = create_api_endpoint_code(service)
    
    # Insert the new code
    lines.insert(insert_line, '')
    lines.insert(insert_line + 1, api_code)
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Updated {file_path}")
    return True

def main():
    """Main function to update all services"""
    print("🚀 Adding standardized /api endpoints to all services...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(services)
    
    for service in services:
        print(f"Processing {service['name']}...")
        if update_service_file(service):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ Successfully updated {success_count}/{total_count} services")
    
    if success_count == total_count:
        print("🎉 All services have been updated with standardized /api endpoints!")
        print("\nYou can now test the endpoints:")
        for service in services:
            print(f"  curl http://localhost:{service['port']}/api")
    else:
        print("⚠️  Some services could not be updated. Check the warnings above.")

if __name__ == "__main__":
    main()
