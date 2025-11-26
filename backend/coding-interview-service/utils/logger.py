"""
Logger utility - imports from text-service
"""

import sys
import os

# Import from text-service
import os
import sys

# Get the text-service logger module directly
current_file_dir = os.path.dirname(os.path.abspath(__file__))
text_service_path = os.path.join(current_file_dir, '..', '..', 'text-service')
text_service_utils_path = os.path.join(text_service_path, 'utils')

if text_service_utils_path not in sys.path:
    sys.path.insert(0, text_service_utils_path)
if text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

# Import from text-service utils.logger (avoid circular import)
import importlib.util
logger_path = os.path.join(text_service_path, 'utils', 'logger.py')
spec = importlib.util.spec_from_file_location("text_service_logger", logger_path)
text_logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(text_logger)

# Export the functions
log_info = text_logger.log_info
log_error = text_logger.log_error
log_warning = text_logger.log_warning

__all__ = ['log_info', 'log_error', 'log_warning']

