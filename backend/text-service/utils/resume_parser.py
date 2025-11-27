"""
Resume Parser Utility
Based on OpenResume project: https://github.com/xitanggg/open-resume
Adapted for SkillScreen AI Interview Assistant

Citation:
Tang, X. (2024). OpenResume: A powerful open-source resume builder and resume parser. 
GitHub. https://github.com/xitanggg/open-resume
"""

import re
import io
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import PyPDF2
import pdfplumber
from .common_utils import (
    validate_email, validate_name, extract_year_from_date, 
    clean_text, calculate_duration_years, sanitize_input
)

class ResumeParser:
    """Enhanced resume parser based on OpenResume project"""
    
    def __init__(self):
        self.name_patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',  # First Last or First Middle Last at start of line
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last (simpler pattern)
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+[A-Z][a-z]+,\s*[A-Z]{2}',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+[A-Z][a-z]+,\s*[A-Z]{2}\s+[A-Z]\d[A-Z]\s*\d[A-Z]\d',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n.*Email',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n.*Phone',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n.*Address',
        ]
        
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        ]
        
        self.skills_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'laravel',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops',
            'machine learning', 'ai', 'tensorflow', 'pytorch', 'scikit-learn',
            'data analysis', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum',
            'linux', 'unix', 'bash', 'powershell', 'shell scripting',
            'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'swift',
            'android', 'ios', 'react native', 'flutter', 'xamarin',
            'tableau', 'power bi', 'excel', 'vba', 'r', 'sas',
            'jira', 'confluence', 'slack', 'teams', 'zoom',
            'photoshop', 'illustrator', 'figma', 'sketch', 'adobe',
            'salesforce', 'hubspot', 'marketo', 'pardot',
            'blockchain', 'ethereum', 'solidity', 'web3',
            'cybersecurity', 'penetration testing', 'ethical hacking',
            'project management', 'leadership', 'team management',
            'communication', 'problem solving', 'analytical thinking'
        ]
        
        self.experience_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b|\bcurrent\b)',
            r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|\bpresent\b|\bcurrent\b)',
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|\bpresent\b|\bcurrent\b)',
        ]

    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF file using multiple methods"""
        try:
            # Method 1: Try pdfplumber first (better for complex layouts)
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)  # Reset file pointer
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}")
            
        try:
            # Method 2: Fallback to PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
            return ""

    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text, filtering out location names"""
        lines = text.split('\n')
        
        # Common location/city names to filter out
        location_names = {
            'scarborough', 'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'edmonton',
            'winnipeg', 'mississauga', 'brampton', 'hamilton', 'london', 'markham', 'vaughan',
            'kitchener', 'windsor', 'saskatoon', 'regina', 'halifax', 'st john', 'victoria',
            'new york', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia',
            'san antonio', 'san diego', 'dallas', 'san jose', 'austin', 'jacksonville',
            'san francisco', 'indianapolis', 'columbus', 'fort worth', 'charlotte', 'seattle',
            'denver', 'washington', 'boston', 'el paso', 'detroit', 'nashville', 'portland',
            'oklahoma city', 'las vegas', 'memphis', 'louisville', 'baltimore', 'milwaukee',
            'albuquerque', 'tucson', 'fresno', 'sacramento', 'kansas city', 'mesa', 'atlanta',
            'omaha', 'colorado springs', 'raleigh', 'miami', 'long beach', 'virginia beach',
            'oakland', 'minneapolis', 'tulsa', 'cleveland', 'wichita', 'arlington'
        }
        
        # Check first few lines for name patterns (increased to 15 lines)
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip lines that are clearly not names
            line_lower = line.lower()
            if any(skip in line_lower for skip in ['resume', 'cv', 'curriculum', 'vitae', 'phone', 'email', 
                                                   'linkedin', 'github', 'objective', 'summary', 'experience',
                                                   'education', 'skills', 'projects', 'contact', 'address']):
                continue
                
            for pattern in self.name_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Validate name (should be 2-4 words, not too long)
                    name_parts = name.split()
                    if 2 <= len(name_parts) <= 4 and len(name) < 50:
                        # Filter out location names
                        if any(part.lower() in location_names for part in name_parts):
                            continue
                        # Check if it's not a common false positive
                        if not any(word.lower() in ['resume', 'cv', 'curriculum', 'vitae', 'profile'] 
                                 for word in name_parts):
                            # Return only first 2-3 words (typically First Last or First Middle Last)
                            # Exclude location names that might be at the end
                            filtered_parts = [part for part in name_parts if part.lower() not in location_names]
                            if len(filtered_parts) >= 2:
                                return ' '.join(filtered_parts[:3]).title()
                            return name.title()
        
        # Fallback: Look for capitalized name pattern in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            # Pattern: First Last or First Middle Last (all capitalized words)
            words = line.split()
            if 2 <= len(words) <= 4:
                # Check if all words start with capital and rest lowercase (typical name pattern)
                if all(w and w[0].isupper() and (len(w) == 1 or w[1:].islower()) for w in words):
                    # Filter out location names
                    filtered_words = [w for w in words if w.lower() not in location_names]
                    if len(filtered_words) >= 2:
                        # Exclude common false positives
                        if not any(w.lower() in ['resume', 'cv', 'phone', 'email', 'linkedin', 'github'] for w in filtered_words):
                            return ' '.join(filtered_words[:3])
        
        return None

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume text with enhanced patterns - checks ALL lines
        Handles patterns like: 'Email: text@gmail.com', 'Contact text@gmail.com', 'text@gmail.com', etc.
        Uses LLM if available for better extraction.
        """
        # Comprehensive email pattern (handles gmail.com, company emails, etc.)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Try LLM-based extraction first if available
        try:
            from services.llm_service import llm_service
            if llm_service.gemini_model:
                # Use LLM to extract email from resume text
                email_extraction_prompt = f"""Extract the email address from the following resume text. Look for patterns like "Email: ...", "Contact: ...", or just the email address itself.

Resume Text (first 2000 characters):
{text[:2000]}

Extract ONLY the email address. Return just the email address, nothing else. If no email is found, return "NOT_FOUND"."""
                
                import asyncio
                loop = asyncio.get_event_loop()
                llm_response = loop.run_until_complete(
                    loop.run_in_executor(
                        None,
                        lambda: llm_service.gemini_model.generate_content(email_extraction_prompt)
                    )
                )
                
                if llm_response and llm_response.text:
                    extracted_email = llm_response.text.strip()
                    # Clean up the response
                    extracted_email = re.sub(r'[^\w.@+-]', '', extracted_email)  # Remove special chars except email chars
                    # Extract email pattern from LLM response
                    email_match = re.search(email_pattern, extracted_email, re.IGNORECASE)
                    if email_match:
                        email = email_match.group(0).lower()
                        if validate_email(email):
                            print(f"[LLM] Extracted email using LLM: {email}")
                            return email
        except Exception as e:
            print(f"[WARNING] LLM email extraction failed: {e}, using rule-based")
        
        # Fallback: Rule-based extraction
        # Split text into lines and check EVERY line (PDFs can have email anywhere)
        lines = text.split('\n')
        found_emails = []
        
        # Strategy 1: Check all lines for email pattern (handles "text@gmail.com" anywhere in line)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Look for email pattern in the line - this will match even if there's text before it
            matches = re.finditer(email_pattern, line, re.IGNORECASE)
            for match in matches:
                email = match.group(0).strip()
                # Clean up common prefixes/suffixes and surrounding text
                email = re.sub(r'^(Email|E-mail|E-Mail|Contact|Mail)[:\s]*', '', email, flags=re.IGNORECASE)
                email = email.strip('.,;:()[]{}"\'')
                # Remove any text that might be before the @ symbol (but keep the email)
                if '@' in email:
                    # Extract just the email part (username@domain)
                    email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', email, re.IGNORECASE)
                    if email_match:
                        email = email_match.group(1)
                if validate_email(email):
                    found_emails.append((i, email.lower()))
        
        # Strategy 2: Check for "Email:" or "Contact:" label pattern in all lines
        # This handles cases like "Email: text@gmail.com" or "Contact text@gmail.com"
        if not found_emails:
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Check for email-related labels
                if any(label in line_lower for label in ['email', 'e-mail', 'contact', 'mail']):
                    # Extract email after colon, space, or label
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            # Look for email in the value part
                            match = re.search(email_pattern, value, re.IGNORECASE)
                            if match:
                                email = match.group(0).strip()
                                email = email.strip('.,;:()[]{}"\'')
                                if validate_email(email):
                                    found_emails.append((i, email.lower()))
                    # Also check if email appears after label word (e.g., "Contact text@gmail.com")
                    match = re.search(r'(?:email|e-mail|contact|mail)[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', line, re.IGNORECASE)
                    if match:
                        email = match.group(1).strip()
                        email = email.strip('.,;:()[]{}"\'')
                        if validate_email(email):
                            found_emails.append((i, email.lower()))
                    # Also check the line itself for any email pattern
                    match = re.search(email_pattern, line, re.IGNORECASE)
                    if match:
                        email = match.group(0).strip()
                        email = email.strip('.,;:()[]{}"\'')
                        if validate_email(email):
                            found_emails.append((i, email.lower()))
        
        # Strategy 3: Search entire text if still not found (fallback)
        if not found_emails:
            matches = re.finditer(email_pattern, text, re.IGNORECASE)
            for match in matches:
                email = match.group(0).strip()
                email = email.strip('.,;:()[]{}"\'')
                if validate_email(email):
                    found_emails.append((0, email.lower()))
                    break  # Take first valid email
        
        # Return the email found earliest in the document (most likely to be the contact email)
        if found_emails:
            # Sort by line number and return the first one
            found_emails.sort(key=lambda x: x[0])
            return found_emails[0][1]
        
        return None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume text"""
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        # Filter out common non-skill words
        exclude_words = {
            'and', 'for', 'with', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were',
            'passion', 'quantum', 'system', 'includes', 'dashboard', 'reports', 'related', 'sales',
            'years', 'experience', 'work', 'job', 'position', 'role', 'company', 'team', 'project'
        }
        
        for skill in self.skills_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Also look for skills mentioned in specific sections
        skills_sections = re.findall(r'(?:skills?|technologies?|tools?|languages?)[:\s]*([^\n]+)', 
                                    text_lower, re.IGNORECASE)
        
        for section in skills_sections:
            # Split by common separators
            skills_in_section = re.split(r'[,;|•\-\n]', section)
            for skill in skills_in_section:
                skill = skill.strip()
                # Better filtering for skills
                if (len(skill) > 2 and 
                    len(skill) < 30 and  # Not too long
                    skill.lower() not in exclude_words and
                    not re.match(r'^[0-9\s]+$', skill) and  # Not just numbers
                    not re.match(r'^[a-z\s]+$', skill) or  # Allow mixed case (programming languages)
                    skill.lower() in [s.lower() for s in self.skills_keywords]):  # Known skills
                    if skill.title() not in found_skills:
                        found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remove duplicates

    def calculate_experience_years(self, text: str) -> float:
        """Calculate total work experience in years (excluding education)"""
        experience_years = 0
        found_dates = set()  # Track dates to avoid double counting
        
        # Split text into sections and exclude education sections
        sections = re.split(r'\n\s*\n', text)
        work_sections = []
        
        for section in sections:
            section_lower = section.lower()
            # Skip education sections
            if any(edu_word in section_lower for edu_word in ['education', 'academic', 'qualification', 'degree', 'university', 'college', 'bachelor', 'master', 'phd']):
                continue
            # Include work-related sections
            if any(work_word in section_lower for work_word in ['experience', 'employment', 'career', 'work', 'professional']):
                work_sections.append(section)
            # Include sections with job titles
            elif any(job_word in section_lower for job_word in ['engineer', 'developer', 'analyst', 'manager', 'consultant', 'specialist', 'lead', 'senior', 'junior', 'intern']):
                work_sections.append(section)
        
        # If no work sections found, use entire text but exclude education patterns
        if not work_sections:
            work_sections = [text]
        
        # Process work sections
        for section in work_sections:
            # Look for date patterns in work context
            date_patterns = [
                r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b|\bcurrent\b)',
                r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|\bpresent\b|\bcurrent\b)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|\bpresent\b|\bcurrent\b)',
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, section, re.IGNORECASE)
                for match in matches:
                    start_date, end_date = match
                    date_key = f"{start_date}-{end_date}"
                    
                    if date_key in found_dates:
                        continue
                    
                    # Parse start date
                    start_year = self._extract_year(start_date)
                    if not start_year:
                        continue
                    
                    # Skip if it's clearly education (before 2015 for most cases)
                    if start_year < 2015:
                        continue
                    
                    # Parse end date
                    if end_date.lower() in ['present', 'current']:
                        end_year = datetime.now().year
                    else:
                        end_year = self._extract_year(end_date)
                        if not end_year:
                            continue
                    
                    # Calculate duration
                    if end_year >= start_year:
                        duration = end_year - start_year
                        # Cap individual job duration at reasonable limit (e.g., 5 years)
                        duration = min(duration, 5)
                        experience_years += duration
                        found_dates.add(date_key)
        
        # Cap total experience at reasonable limit
        return min(max(0, experience_years), 10)

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        # Look for 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return int(year_match.group(0))
        return None

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        # Look for education section
        education_patterns = [
            r'(?:education|academic|qualification)[:\s]*([^\n]+(?:\n[^\n]+)*)',
            r'(bachelor|master|phd|doctorate|diploma|certificate)[:\s]*([^\n]+)',
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    education.append({
                        'degree': match[0].strip(),
                        'details': match[1].strip() if len(match) > 1 else ''
                    })
                else:
                    education.append({
                        'degree': match.strip(),
                        'details': ''
                    })
        
        return education

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        experience = []
        
        # Look for experience section
        experience_patterns = [
            r'(?:experience|work history|employment|career)[:\s]*([^\n]+(?:\n[^\n]+)*)',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–]\s*([^\n]+)',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    experience.append({
                        'company': match[0].strip(),
                        'details': match[1].strip()
                    })
                elif isinstance(match, str):
                    experience.append({
                        'company': match.strip(),
                        'details': ''
                    })
        
        return experience

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured information"""
        if not resume_text or not resume_text.strip():
            return {
                'name': None,
                'email': None,
                'phone': None,
                'skills': [],
                'experience_years': 0,
                'education': [],
                'work_experience': [],
                'raw_text': resume_text
            }
        
        return {
            'name': self.extract_name(resume_text),
            'email': self.extract_email(resume_text),
            'phone': self.extract_phone(resume_text),
            'skills': self.extract_skills(resume_text),
            'experience_years': self.calculate_experience_years(resume_text),
            'education': self.extract_education(resume_text),
            'work_experience': self.extract_experience(resume_text),
            'raw_text': resume_text
        }

    def parse_resume_from_pdf(self, pdf_file) -> Dict[str, Any]:
        """Parse resume from PDF file"""
        text = self.extract_text_from_pdf(pdf_file)
        return self.parse_resume(text)

# Global instance
resume_parser = ResumeParser()
