"""
Common utility functions to reduce code duplication
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_name(name: str) -> bool:
    """Validate name format"""
    if not name or len(name.strip()) < 2:
        return False
    # Check if name contains only letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']+$"
    return bool(re.match(pattern, name.strip()))


def extract_year_from_date(date_str: str) -> Optional[int]:
    """Extract year from various date formats"""
    if not date_str:
        return None
    
    # Common date patterns
    patterns = [
        r'(\d{4})',  # Just year
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
        r'(\w+)\s+(\d{4})',  # Month Year
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            # Return the year (usually the last group)
            year = int(match.groups()[-1])
            if 1900 <= year <= datetime.now().year + 1:
                return year
    
    return None


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-.,!?@#$%&*()+=:;"\'<>/\\]', '', text)
    
    return text


def calculate_duration_years(start_date: str, end_date: str) -> float:
    """Calculate duration in years between two dates"""
    start_year = extract_year_from_date(start_date)
    end_year = extract_year_from_date(end_date)
    
    if not start_year or not end_year:
        return 0.0
    
    if end_year < start_year:
        return 0.0
    
    return end_year - start_year


def format_response_data(data: Dict[str, Any], status: str = "success") -> Dict[str, Any]:
    """Format API response data consistently"""
    return {
        "status": status,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "message": "Operation completed successfully" if status == "success" else "Operation failed"
    }


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that required fields are present in data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    return missing_fields


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Limit length
    text = text[:max_length]
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Clean whitespace
    text = clean_text(text)
    
    return text


def extract_skills_from_text(text: str, skill_keywords: List[str]) -> List[str]:
    """Extract skills from text using keyword matching"""
    if not text or not skill_keywords:
        return []
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates


def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"session_{uuid.uuid4().hex[:8]}"


def log_api_call(endpoint: str, method: str, status_code: int, duration: float):
    """Log API call details"""
    from utils.logger import log_info
    log_info(f"API Call: {method} {endpoint} - Status: {status_code} - Duration: {duration:.2f}s")


def validate_job_data(job_data: Dict[str, Any]) -> List[str]:
    """Validate job data structure"""
    required_fields = ["title", "company", "description"]
    missing_fields = validate_required_fields(job_data, required_fields)
    
    # Additional validations
    if "required_skills" in job_data and not isinstance(job_data["required_skills"], list):
        missing_fields.append("required_skills (must be a list)")
    
    return missing_fields


def validate_candidate_data(candidate_data: Dict[str, Any]) -> List[str]:
    """Validate candidate data structure"""
    required_fields = ["name", "email", "resume_text"]
    missing_fields = validate_required_fields(candidate_data, required_fields)
    
    # Additional validations
    if "email" in candidate_data and not validate_email(candidate_data["email"]):
        missing_fields.append("email (invalid format)")
    
    if "name" in candidate_data and not validate_name(candidate_data["name"]):
        missing_fields.append("name (invalid format)")
    
    return missing_fields
