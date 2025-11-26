"""
Startup script for Coding Interview Service
Handles all path setup before starting the FastAPI app
"""

import os
import sys

# Get the project root
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
text_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))
coding_service_path = current_file_dir

# Add paths
if coding_service_path not in sys.path:
    sys.path.insert(0, coding_service_path)
if text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

# Change to coding service directory
os.chdir(coding_service_path)

# Now import and run the app
if __name__ == "__main__":
    import uvicorn
    print(f"Starting Coding Interview Service on port 8001...")
    print(f"Project root: {project_root}")
    print(f"Text service path: {text_service_path}")
    print(f"Coding service path: {coding_service_path}")
    
    # Import app after paths are set
    from app import app
    
    # Use string import for reload to work properly
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload for now to avoid import issues
        log_level="info"
    )

