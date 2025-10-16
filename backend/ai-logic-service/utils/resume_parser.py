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

class ResumeParser:
    """Enhanced resume parser based on OpenResume project"""
    
    def __init__(self):
        self.name_patterns = [
            r'^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
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
        """Extract candidate name from resume text"""
        lines = text.split('\n')
        
        # Check first few lines for name patterns
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if not line:
                continue
                
            for pattern in self.name_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Validate name (should be 2-3 words, not too long)
                    name_parts = name.split()
                    if 2 <= len(name_parts) <= 3 and len(name) < 50:
                        # Check if it's not a common false positive
                        if not any(word.lower() in ['resume', 'cv', 'curriculum', 'vitae', 'profile'] 
                                 for word in name_parts):
                            return name.title()
        
        return None

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume text"""
        match = re.search(self.email_pattern, text)
        return match.group(0) if match else None

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
        
        for skill in self.skills_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Also look for skills mentioned in specific sections
        skills_sections = re.findall(r'(?:skills?|technologies?|technologies?|tools?|languages?)[:\s]*([^\n]+)', 
                                    text_lower, re.IGNORECASE)
        
        for section in skills_sections:
            # Split by common separators
            skills_in_section = re.split(r'[,;|•\-\n]', section)
            for skill in skills_in_section:
                skill = skill.strip()
                if len(skill) > 2 and skill not in found_skills:
                    found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remove duplicates

    def calculate_experience_years(self, text: str) -> float:
        """Calculate total work experience in years"""
        experience_years = 0
        
        # Look for experience patterns
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                start_date, end_date = match
                
                # Parse start date
                start_year = self._extract_year(start_date)
                if not start_year:
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
                    experience_years += duration
        
        return max(0, experience_years)

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
