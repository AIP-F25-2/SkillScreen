"""
Resume Parser for SkillScreen
Extracts skills, experience, and qualifications from resumes
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Experience:
    """Experience entry from resume"""
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    description: str = ""
    skills_mentioned: List[str] = None
    
    def __post_init__(self):
        if self.skills_mentioned is None:
            self.skills_mentioned = []

@dataclass
class Education:
    """Education entry from resume"""
    institution: str
    degree: str
    field: str = ""
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

@dataclass
class ParsedResume:
    """Complete parsed resume data"""
    name: str
    email: str
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: List[str] = None
    experience: List[Experience] = None
    education: List[Education] = None
    certifications: List[str] = None
    projects: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.experience is None:
            self.experience = []
        if self.education is None:
            self.education = []
        if self.certifications is None:
            self.certifications = []
        if self.projects is None:
            self.projects = []

class ResumeParser:
    """Main resume parsing class"""
    
    def __init__(self):
        """Initialize the resume parser"""
        self.nlp = None
        self.stop_words = set(stopwords.words('english'))
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Technical skills database
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql',
                'html', 'css', 'xml', 'yaml', 'json', 'bash', 'powershell'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
                'spring', 'spring boot', 'laravel', 'rails', 'asp.net', 'jquery',
                'bootstrap', 'tailwind', 'sass', 'less', 'webpack', 'babel'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
                'oracle', 'sqlite', 'dynamodb', 'neo4j', 'influxdb', 'couchdb'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'amazon web services',
                'microsoft azure', 'heroku', 'digital ocean', 'linode'
            ],
            'tools': [
                'git', 'github', 'gitlab', 'jenkins', 'docker', 'kubernetes',
                'terraform', 'ansible', 'chef', 'puppet', 'vagrant', 'jira',
                'confluence', 'slack', 'teams', 'zoom', 'figma', 'sketch'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd',
                'microservices', 'api', 'rest', 'graphql', 'soa', 'mvc'
            ]
        }
        
        # Soft skills keywords
        self.soft_skills = [
            'leadership', 'communication', 'teamwork', 'problem solving',
            'analytical', 'creative', 'adaptable', 'organized', 'detail oriented',
            'time management', 'project management', 'mentoring', 'collaboration',
            'presentation', 'negotiation', 'customer service', 'critical thinking'
        ]
    
    def parse_resume(self, resume_text: str) -> ParsedResume:
        """Parse resume text and extract structured information"""
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(resume_text)
            
            # Extract basic information
            name = self._extract_name(cleaned_text)
            email = self._extract_email(cleaned_text)
            phone = self._extract_phone(cleaned_text)
            location = self._extract_location(cleaned_text)
            
            # Extract sections
            summary = self._extract_summary(cleaned_text)
            skills = self._extract_skills(cleaned_text)
            experience = self._extract_experience(cleaned_text)
            education = self._extract_education(cleaned_text)
            certifications = self._extract_certifications(cleaned_text)
            projects = self._extract_projects(cleaned_text)
            
            return ParsedResume(
                name=name,
                email=email,
                phone=phone,
                location=location,
                summary=summary,
                skills=skills,
                experience=experience,
                education=education,
                certifications=certifications,
                projects=projects
            )
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            return ParsedResume(name="Unknown", email="")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize resume text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-/]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name from resume"""
        # Look for name patterns at the beginning
        lines = text.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 0 and len(line.split()) <= 4:  # Name is usually 1-4 words
                # Check if line doesn't contain common resume keywords
                if not any(keyword in line.lower() for keyword in [
                    'email', 'phone', 'address', 'linkedin', 'github', 'objective',
                    'summary', 'experience', 'education', 'skills', 'projects'
                ]):
                    return line
        
        return "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from resume"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume"""
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        return ""
    
    def _extract_location(self, text: str) -> str:
        """Extract location from resume"""
        # Look for location patterns
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, State
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2})',  # City, State, Country
        ]
        
        for pattern in location_patterns:
            locations = re.findall(pattern, text)
            if locations:
                return locations[0].strip()
        
        return ""
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary/objective"""
        summary_keywords = ['summary', 'objective', 'profile', 'about', 'overview']
        
        for keyword in summary_keywords:
            pattern = rf'{keyword}[:\s]*(.*?)(?=\n\s*[A-Z]|\n\s*[a-z]|\n\s*\d|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 20:  # Valid summary should be substantial
                    return summary[:500]  # Limit length
        
        return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and soft skills"""
        skills = set()
        text_lower = text.lower()
        
        # Extract technical skills
        for category, skill_list in self.technical_skills.items():
            for skill in skill_list:
                if skill.lower() in text_lower:
                    skills.add(skill.title())
        
        # Extract soft skills
        for skill in self.soft_skills:
            if skill.lower() in text_lower:
                skills.add(skill.title())
        
        # Extract skills from "Skills" section
        skills_section = self._extract_section(text, ['skills', 'technical skills', 'core competencies'])
        if skills_section:
            # Split by common delimiters
            skill_items = re.split(r'[,;•\n]', skills_section)
            for item in skill_items:
                item = item.strip()
                if len(item) > 1 and len(item) < 50:  # Reasonable skill length
                    skills.add(item.title())
        
        return list(skills)
    
    def _extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience"""
        experience = []
        
        # Look for experience section
        exp_section = self._extract_section(text, ['experience', 'work experience', 'employment', 'career'])
        if not exp_section:
            return experience
        
        # Split into individual experiences
        exp_entries = re.split(r'\n(?=\w)', exp_section)
        
        for entry in exp_entries:
            if len(entry.strip()) < 20:  # Skip very short entries
                continue
                
            exp = self._parse_experience_entry(entry)
            if exp:
                experience.append(exp)
        
        return experience
    
    def _parse_experience_entry(self, entry: str) -> Optional[Experience]:
        """Parse individual experience entry"""
        lines = entry.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # Extract company and position from first line
        first_line = lines[0].strip()
        
        # Try to extract dates
        date_pattern = r'(\d{4}|\w+\s+\d{4}|\d{1,2}/\d{4}|\d{1,2}-\d{4})'
        dates = re.findall(date_pattern, first_line)
        
        # Extract company and position
        company = ""
        position = ""
        
        # Common patterns: "Position at Company" or "Company - Position"
        if ' at ' in first_line:
            parts = first_line.split(' at ')
            position = parts[0].strip()
            company = parts[1].strip()
        elif ' - ' in first_line:
            parts = first_line.split(' - ')
            company = parts[0].strip()
            position = parts[1].strip()
        else:
            # Try to extract from the line
            words = first_line.split()
            if len(words) >= 2:
                position = ' '.join(words[:-1])
                company = words[-1]
        
        # Extract description
        description = '\n'.join(lines[1:]).strip()
        
        # Extract skills mentioned in this experience
        skills_mentioned = []
        for skill_list in self.technical_skills.values():
            for skill in skill_list:
                if skill.lower() in description.lower():
                    skills_mentioned.append(skill.title())
        
        return Experience(
            company=company,
            position=position,
            description=description,
            skills_mentioned=skills_mentioned
        )
    
    def _extract_education(self, text: str) -> List[Education]:
        """Extract education information"""
        education = []
        
        # Look for education section
        edu_section = self._extract_section(text, ['education', 'academic', 'qualifications'])
        if not edu_section:
            return education
        
        # Split into individual education entries
        edu_entries = re.split(r'\n(?=\w)', edu_section)
        
        for entry in edu_entries:
            if len(entry.strip()) < 10:
                continue
                
            edu = self._parse_education_entry(entry)
            if edu:
                education.append(edu)
        
        return education
    
    def _parse_education_entry(self, entry: str) -> Optional[Education]:
        """Parse individual education entry"""
        lines = entry.strip().split('\n')
        if len(lines) < 1:
            return None
        
        first_line = lines[0].strip()
        
        # Extract degree and institution
        degree_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma', 'certificate']
        
        institution = first_line
        degree = ""
        field = ""
        
        for keyword in degree_keywords:
            if keyword.lower() in first_line.lower():
                # Extract degree information
                degree_match = re.search(rf'({keyword}[^,]*?)(?:,|in|of)', first_line, re.IGNORECASE)
                if degree_match:
                    degree = degree_match.group(1).strip()
                
                # Extract field of study
                field_match = re.search(rf'(?:in|of)\s+([^,]+)', first_line, re.IGNORECASE)
                if field_match:
                    field = field_match.group(1).strip()
                
                break
        
        return Education(
            institution=institution,
            degree=degree,
            field=field
        )
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        # Look for certifications section
        cert_section = self._extract_section(text, ['certifications', 'certificates', 'licenses'])
        if cert_section:
            cert_items = re.split(r'[,;•\n]', cert_section)
            for item in cert_items:
                item = item.strip()
                if len(item) > 3:
                    certifications.append(item)
        
        return certifications
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract projects"""
        projects = []
        
        # Look for projects section
        proj_section = self._extract_section(text, ['projects', 'portfolio', 'key projects'])
        if proj_section:
            proj_items = re.split(r'\n(?=\w)', proj_section)
            for item in proj_items:
                item = item.strip()
                if len(item) > 10:
                    projects.append(item)
        
        return projects
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a specific section from resume text"""
        for section_name in section_names:
            pattern = rf'{section_name}[:\s]*(.*?)(?=\n\s*[A-Z][a-z]*[:\s]|\n\s*[A-Z][A-Z]|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def get_skill_categories(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into different types"""
        categorized = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'cloud_platforms': [],
            'tools': [],
            'methodologies': [],
            'soft_skills': [],
            'other': []
        }
        
        for skill in skills:
            skill_lower = skill.lower()
            categorized_flag = False
            
            for category, skill_list in self.technical_skills.items():
                if skill_lower in [s.lower() for s in skill_list]:
                    categorized[category].append(skill)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                if skill_lower in [s.lower() for s in self.soft_skills]:
                    categorized['soft_skills'].append(skill)
                else:
                    categorized['other'].append(skill)
        
        return categorized
    
    def calculate_experience_years(self, experience: List[Experience]) -> float:
        """Calculate total years of experience"""
        total_months = 0
        
        for exp in experience:
            if exp.duration:
                # Parse duration (e.g., "2 years", "18 months")
                duration_match = re.search(r'(\d+)\s*(year|month)', exp.duration.lower())
                if duration_match:
                    value = int(duration_match.group(1))
                    unit = duration_match.group(2)
                    if unit == 'year':
                        total_months += value * 12
                    else:
                        total_months += value
        
        return total_months / 12.0
    
    def generate_skill_summary(self, parsed_resume: ParsedResume) -> str:
        """Generate a summary of candidate skills"""
        categorized_skills = self.get_skill_categories(parsed_resume.skills)
        
        summary_parts = []
        
        if categorized_skills['programming_languages']:
            summary_parts.append(f"Programming Languages: {', '.join(categorized_skills['programming_languages'][:5])}")
        
        if categorized_skills['frameworks']:
            summary_parts.append(f"Frameworks: {', '.join(categorized_skills['frameworks'][:5])}")
        
        if categorized_skills['databases']:
            summary_parts.append(f"Databases: {', '.join(categorized_skills['databases'][:3])}")
        
        if categorized_skills['cloud_platforms']:
            summary_parts.append(f"Cloud Platforms: {', '.join(categorized_skills['cloud_platforms'][:3])}")
        
        if categorized_skills['tools']:
            summary_parts.append(f"Tools: {', '.join(categorized_skills['tools'][:5])}")
        
        if categorized_skills['soft_skills']:
            summary_parts.append(f"Soft Skills: {', '.join(categorized_skills['soft_skills'][:3])}")
        
        return '; '.join(summary_parts)