"""
Code Execution Service for Coding Interview
Reuses code execution from text-service
"""

import sys
import os

# Import from text-service
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
text_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))
coding_service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add paths
if text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)
if coding_service_dir not in sys.path:
    sys.path.insert(0, coding_service_dir)

from services.code_execution_service import CodeExecutionService as BaseCodeExecutionService

class CodeExecutionService(BaseCodeExecutionService):
    """Code execution service for coding interviews"""
    
    def __init__(self):
        super().__init__()
        # Additional initialization if needed
        pass

