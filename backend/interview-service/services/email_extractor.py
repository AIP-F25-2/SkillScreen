import re
import logging
from typing import List, Dict, Any, Optional
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class EmailExtractor:
    """Extracts email addresses and names from text content"""
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Name patterns (common resume name formats) - ordered by priority
    # Using non-backtracking patterns to avoid ReDoS vulnerability
    NAME_PATTERNS = [
        # Most specific patterns first
        r'(?:Name|Full Name|Candidate Name)[\s:]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*$',  # First Last at start of line (standalone)
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n',  # First Last at start of line followed by newline
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+Email',  # Name followed by Email
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+Phone',  # Name followed by Phone
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*@',  # Name followed by @ (email)
        # Less specific patterns (avoid job titles)
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last at start of line (fallback)
    ]
    
    # Job titles to exclude from name extraction
    JOB_TITLES = [
        'software engineer', 'data scientist', 'product manager', 'project manager',
        'business analyst', 'system administrator', 'devops engineer', 'frontend developer',
        'backend developer', 'full stack developer', 'mobile developer', 'ui designer',
        'ux designer', 'graphic designer', 'marketing manager', 'sales manager',
        'hr manager', 'financial analyst', 'accountant', 'consultant', 'architect',
        'senior', 'junior', 'lead', 'principal', 'director', 'manager', 'analyst',
        'developer', 'engineer', 'designer', 'specialist', 'coordinator', 'assistant'
    ]
    
    def __init__(self):
        self.compiled_name_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                     for pattern in self.NAME_PATTERNS]
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract and validate email addresses from text"""
        if not text:
            return []
        
        # Clean text by removing extra spaces around @ and . characters
        # Use a safer approach that handles spaces without ReDoS vulnerability
        # Replace spaces around @ symbol
        cleaned_text = text.replace(' @', '@').replace('@ ', '@')
        # Replace spaces around . symbol  
        cleaned_text = cleaned_text.replace(' .', '.').replace('. ', '.')
        
        logger.debug(f"Original text sample: {text[:200]}...")
        logger.debug(f"Cleaned text sample: {cleaned_text[:200]}...")
        
        # Find all email matches
        email_matches = self.EMAIL_PATTERN.findall(cleaned_text)
        logger.debug(f"Found {len(email_matches)} email matches: {email_matches}")
        
        # Validate emails
        valid_emails = []
        for email in email_matches:
            try:
                # Validate email format
                validated_email = validate_email(email)
                valid_emails.append(validated_email.email.lower())
            except EmailNotValidError:
                logger.debug(f"Invalid email format: {email}")
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in valid_emails:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)
        
        return unique_emails
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from text"""
        if not text:
            return None
        
        logger.info("Starting name extraction...")
        
        # Try first line method
        name = self._try_first_line_method(text)
        if name:
            return name
        
        # Try pattern matching method
        name = self._try_pattern_matching_method(text)
        if name:
            return name
        
        logger.info("No valid name found")
        return None
    
    def _try_first_line_method(self, text: str) -> Optional[str]:
        """Try to extract name from first line"""
        first_line = self._get_first_line(text)
        if first_line and self._is_valid_name(first_line):
            first_line_lower = first_line.lower()
            if not any(job_title in first_line_lower for job_title in self.JOB_TITLES):
                logger.info(f"Using first line as name: {first_line}")
                return first_line.title()
        return None
    
    def _try_pattern_matching_method(self, text: str) -> Optional[str]:
        """Try to extract name using pattern matching"""
        logger.info("First line method didn't work, trying patterns...")
        
        for i, pattern in enumerate(self.compiled_name_patterns):
            matches = pattern.findall(text)
            if matches:
                logger.info(f"Pattern {i} found matches: {matches}")
                for match in matches:
                    name = self._process_pattern_match(match)
                    if name:
                        return name
        return None
    
    def _process_pattern_match(self, match: str) -> Optional[str]:
        """Process a pattern match to extract valid name"""
        # Clean up the match
        name = match.strip()
        name = re.sub(r'\s+', ' ', name)
        # Use non-backtracking pattern to avoid ReDoS vulnerability
        name = re.sub(r'^(Mr\.|Ms\.|Mrs\.|Dr\.)\s+', '', name, flags=re.IGNORECASE)
        
        logger.info(f"Cleaned name: '{name}'")
        
        # Basic validation - should have at least first and last name
        name_parts = name.split()
        if len(name_parts) < 2:
            return None
        
        # Check if it's not a job title or section header
        if self._is_job_title_or_section_header(name):
            return None
        
        # Additional validation: check if it looks like a real name
        if self._is_valid_name(name):
            logger.info(f"Using pattern match as name: {name}")
            return name.title()
        
        return None
    
    def _is_job_title_or_section_header(self, name: str) -> bool:
        """Check if the name is actually a job title or section header"""
        name_lower = name.lower()
        
        # Check for job titles
        if any(job_title in name_lower for job_title in self.JOB_TITLES):
            return True
        
        # Check for section headers
        section_headers = [
            'technical', 'skills', 'experience', 'education', 'projects', 
            'summary', 'objective', 'profile', 'contact', 'phone', 'email',
            'address', 'linkedin', 'github', 'portfolio', 'certifications'
        ]
        return any(skip_word in name_lower for skip_word in section_headers)
    
    def _get_first_line(self, text: str) -> Optional[str]:
        """Get the first non-empty line from the text"""
        lines = text.strip().split('\n')
        logger.info(f"First 10 lines of text: {lines[:10]}")
        
        # Look for name patterns in the first 10 lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and len(line) > 3:  # Skip very short lines
                logger.info(f"Checking line {i}: '{line}'")
                
                if self._is_potential_name_line(line):
                    logger.info(f"Found potential name: '{line}'")
                    return line
        return None
    
    def _is_potential_name_line(self, line: str) -> bool:
        """Check if a line looks like a potential name"""
        # Check if it looks like a name (2-4 words, all starting with capital letters)
        words = line.split()
        if not (2 <= len(words) <= 4):
            return False
        
        if not all(word[0].isupper() and word.isalpha() for word in words):
            return False
        
        # Additional check: make sure it's not a section header or common resume words
        return not self._is_section_header(line)
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        line_lower = line.lower()
        section_headers = [
            'technical', 'skills', 'experience', 'education', 'projects', 
            'summary', 'objective', 'profile', 'contact', 'phone', 'email',
            'address', 'linkedin', 'github', 'portfolio', 'certifications'
        ]
        return any(skip_word in line_lower for skip_word in section_headers)
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if the extracted text looks like a valid name"""
        name_parts = name.split()
        
        # Must have at least 2 parts
        if len(name_parts) < 2:
            return False
        
        # Each part should start with capital letter
        for part in name_parts:
            if not part[0].isupper():
                return False
        
        # Should not contain numbers or special characters (except hyphens for compound names)
        # Use non-backtracking pattern to avoid ReDoS vulnerability
        for part in name_parts:
            if not re.match(r'^[A-Za-z-]+$', part):
                return False
        
        # Should not be too long (avoid extracting long phrases)
        if len(name) > 50:
            return False
        
        return True
    
    def extract_candidate_info(self, text: str) -> Dict[str, Any]:
        """Extract both email and name from text"""
        emails = self.extract_emails(text)
        name = self.extract_name(text)
        
        return {
            "emails": emails,
            "name": name,
            "email_count": len(emails)
        }
