"""
Job Description Parser for SkillScreen
Extracts skills, requirements, and qualifications from job descriptions
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
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
class JobRequirement:
    """Job requirement entry"""
    requirement: str
    category: str  # 'required', 'preferred', 'nice_to_have'
    skill_type: str  # 'technical', 'soft', 'experience'
    importance: float  # 0.0 to 1.0

@dataclass
class ParsedJobDescription:
    """Complete parsed job description data"""
    title: str
    company: str
    location: str = ""
    job_type: str = ""  # full-time, part-time, contract, etc.
    experience_level: str = ""  # entry, mid, senior, lead
    salary_range: str = ""
    description: str = ""
    requirements: List[JobRequirement] = None
    responsibilities: List[str] = None
    benefits: List[str] = None
    skills_required: List[str] = None
    skills_preferred: List[str] = None
    education_requirements: List[str] = None
    experience_years: Optional[int] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.responsibilities is None:
            self.responsibilities = []
        if self.benefits is None:
            self.benefits = []
        if self.skills_required is None:
            self.skills_required = []
        if self.skills_preferred is None:
            self.skills_preferred = []
        if self.education_requirements is None:
            self.education_requirements = []

class JobParser:
    """Main job description parsing class"""
    
    def __init__(self):
        """Initialize the job parser"""
        self.nlp = None
        self.stop_words = set(stopwords.words('english'))
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Technical skills database (same as resume parser)
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
        
        # Experience level keywords
        self.experience_levels = {
            'entry': ['entry level', 'junior', 'graduate', 'intern', '0-2 years', '1-2 years'],
            'mid': ['mid level', 'intermediate', '3-5 years', '4-6 years', 'experienced'],
            'senior': ['senior', 'lead', 'principal', '5+ years', '7+ years', '8+ years'],
            'executive': ['director', 'vp', 'vice president', 'cto', 'cfo', 'ceo']
        }
    
    def parse_job_description(self, job_text: str) -> ParsedJobDescription:
        """Parse job description text and extract structured information"""
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(job_text)
            
            # Extract basic information
            title = self._extract_job_title(cleaned_text)
            company = self._extract_company(cleaned_text)
            location = self._extract_location(cleaned_text)
            job_type = self._extract_job_type(cleaned_text)
            experience_level = self._extract_experience_level(cleaned_text)
            salary_range = self._extract_salary_range(cleaned_text)
            
            # Extract sections
            description = self._extract_description(cleaned_text)
            requirements = self._extract_requirements(cleaned_text)
            responsibilities = self._extract_responsibilities(cleaned_text)
            benefits = self._extract_benefits(cleaned_text)
            
            # Extract skills and education
            skills_required = self._extract_required_skills(cleaned_text)
            skills_preferred = self._extract_preferred_skills(cleaned_text)
            education_requirements = self._extract_education_requirements(cleaned_text)
            experience_years = self._extract_experience_years(cleaned_text)
            
            return ParsedJobDescription(
                title=title,
                company=company,
                location=location,
                job_type=job_type,
                experience_level=experience_level,
                salary_range=salary_range,
                description=description,
                requirements=requirements,
                responsibilities=responsibilities,
                benefits=benefits,
                skills_required=skills_required,
                skills_preferred=skills_preferred,
                education_requirements=education_requirements,
                experience_years=experience_years
            )
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            return ParsedJobDescription(title="Unknown", company="Unknown")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize job description text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-/]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _extract_job_title(self, text: str) -> str:
        """Extract job title from job description"""
        # Look for title patterns at the beginning
        lines = text.split('\n')[:3]  # Check first 3 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 0 and len(line.split()) <= 6:  # Title is usually 1-6 words
                # Check if line doesn't contain common job description keywords
                if not any(keyword in line.lower() for keyword in [
                    'company', 'location', 'salary', 'benefits', 'requirements',
                    'responsibilities', 'description', 'about', 'overview'
                ]):
                    return line
        
        return "Unknown Position"
    
    def _extract_company(self, text: str) -> str:
        """Extract company name from job description"""
        # Look for company patterns
        company_patterns = [
            r'at\s+([A-Za-z\s&]+?)(?:\s+is|\s+seeks|\s+is\s+looking)',
            r'([A-Za-z\s&]+?)\s+is\s+hiring',
            r'([A-Za-z\s&]+?)\s+seeks',
            r'([A-Za-z\s&]+?)\s+is\s+looking'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                company = matches[0].strip()
                if len(company) > 2 and len(company) < 50:
                    return company
        
        return "Unknown Company"
    
    def _extract_location(self, text: str) -> str:
        """Extract job location from job description"""
        # Look for location patterns
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, State
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2})',  # City, State, Country
            r'(remote|hybrid|on-site|onsite)',
            r'(work\s+from\s+home|wfh)'
        ]
        
        for pattern in location_patterns:
            locations = re.findall(pattern, text, re.IGNORECASE)
            if locations:
                return locations[0].strip()
        
        return ""
    
    def _extract_job_type(self, text: str) -> str:
        """Extract job type from job description"""
        job_types = {
            'full-time': ['full time', 'full-time', 'permanent', 'ft'],
            'part-time': ['part time', 'part-time', 'pt'],
            'contract': ['contract', 'contractor', 'freelance', 'consultant'],
            'internship': ['intern', 'internship', 'trainee'],
            'temporary': ['temp', 'temporary', 'temporary position']
        }
        
        text_lower = text.lower()
        for job_type, keywords in job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return job_type
        
        return "full-time"  # Default assumption
    
    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from job description"""
        text_lower = text.lower()
        
        for level, keywords in self.experience_levels.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        
        return "mid"  # Default assumption
    
    def _extract_salary_range(self, text: str) -> str:
        """Extract salary range from job description"""
        salary_patterns = [
            r'\$[\d,]+(?:k|K)?\s*[-–]\s*\$[\d,]+(?:k|K)?',
            r'\$[\d,]+(?:k|K)?\s*to\s*\$[\d,]+(?:k|K)?',
            r'\$[\d,]+(?:k|K)?\s*-\s*\$[\d,]+(?:k|K)?',
            r'salary:\s*\$[\d,]+(?:k|K)?\s*[-–]\s*\$[\d,]+(?:k|K)?'
        ]
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def _extract_description(self, text: str) -> str:
        """Extract job description/overview"""
        description_keywords = ['description', 'overview', 'about', 'summary', 'role']
        
        for keyword in description_keywords:
            pattern = rf'{keyword}[:\s]*(.*?)(?=\n\s*(?:requirements|responsibilities|qualifications|benefits)|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                if len(description) > 50:  # Valid description should be substantial
                    return description[:1000]  # Limit length
        
        return ""
    
    def _extract_requirements(self, text: str) -> List[JobRequirement]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements section
        req_section = self._extract_section(text, ['requirements', 'qualifications', 'must have', 'required'])
        if not req_section:
            return requirements
        
        # Split into individual requirements
        req_items = re.split(r'[•\n]', req_section)
        
        for item in req_items:
            item = item.strip()
            if len(item) < 10:  # Skip very short items
                continue
            
            # Determine category and importance
            category = 'required'
            importance = 1.0
            
            if any(word in item.lower() for word in ['preferred', 'nice to have', 'bonus', 'plus']):
                category = 'preferred'
                importance = 0.7
            elif any(word in item.lower() for word in ['must', 'required', 'essential', 'mandatory']):
                category = 'required'
                importance = 1.0
            
            # Determine skill type
            skill_type = 'technical'
            if any(skill in item.lower() for skill in self.soft_skills):
                skill_type = 'soft'
            elif any(word in item.lower() for word in ['years', 'experience', 'minimum']):
                skill_type = 'experience'
            
            requirements.append(JobRequirement(
                requirement=item,
                category=category,
                skill_type=skill_type,
                importance=importance
            ))
        
        return requirements
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for responsibilities section
        resp_section = self._extract_section(text, ['responsibilities', 'duties', 'what you will do', 'key responsibilities'])
        if resp_section:
            resp_items = re.split(r'[•\n]', resp_section)
            for item in resp_items:
                item = item.strip()
                if len(item) > 10:
                    responsibilities.append(item)
        
        return responsibilities
    
    def _extract_benefits(self, text: str) -> List[str]:
        """Extract job benefits"""
        benefits = []
        
        # Look for benefits section
        benefits_section = self._extract_section(text, ['benefits', 'perks', 'compensation', 'what we offer'])
        if benefits_section:
            benefit_items = re.split(r'[•\n]', benefits_section)
            for item in benefit_items:
                item = item.strip()
                if len(item) > 5:
                    benefits.append(item)
        
        return benefits
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description"""
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
        
        return list(skills)
    
    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred skills from job description"""
        skills = set()
        
        # Look for preferred skills section
        preferred_section = self._extract_section(text, ['preferred', 'nice to have', 'bonus', 'plus'])
        if preferred_section:
            text_lower = preferred_section.lower()
            
            # Extract technical skills
            for category, skill_list in self.technical_skills.items():
                for skill in skill_list:
                    if skill.lower() in text_lower:
                        skills.add(skill.title())
            
            # Extract soft skills
            for skill in self.soft_skills:
                if skill.lower() in text_lower:
                    skills.add(skill.title())
        
        return list(skills)
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements"""
        education = []
        
        # Look for education section
        edu_section = self._extract_section(text, ['education', 'degree', 'qualifications'])
        if edu_section:
            edu_items = re.split(r'[•\n]', edu_section)
            for item in edu_items:
                item = item.strip()
                if len(item) > 5:
                    education.append(item)
        
        return education
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract required years of experience"""
        # Look for experience patterns
        experience_patterns = [
            r'(\d+)\s*years?\s*of\s*experience',
            r'(\d+)\+?\s*years?\s*experience',
            r'minimum\s*of\s*(\d+)\s*years?',
            r'at\s*least\s*(\d+)\s*years?'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return int(matches[0])
        
        return None
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a specific section from job description text"""
        for section_name in section_names:
            pattern = rf'{section_name}[:\s]*(.*?)(?=\n\s*[A-Z][a-z]*[:\s]|\n\s*[A-Z][A-Z]|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def generate_skill_gaps(self, job_skills: List[str], candidate_skills: List[str]) -> Dict[str, List[str]]:
        """Generate skill gaps between job requirements and candidate skills"""
        job_skills_lower = [skill.lower() for skill in job_skills]
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        
        missing_skills = []
        matching_skills = []
        
        for skill in job_skills:
            if skill.lower() in candidate_skills_lower:
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'match_percentage': len(matching_skills) / len(job_skills) * 100 if job_skills else 0
        }
    
    def generate_interview_focus_areas(self, parsed_job: ParsedJobDescription) -> List[str]:
        """Generate focus areas for interview based on job requirements"""
        focus_areas = []
        
        # Add technical skills focus
        if parsed_job.skills_required:
            focus_areas.extend([f"Technical expertise in {skill}" for skill in parsed_job.skills_required[:5]])
        
        # Add experience level focus
        if parsed_job.experience_level:
            focus_areas.append(f"{parsed_job.experience_level.title()} level experience")
        
        # Add specific requirements focus
        for req in parsed_job.requirements[:3]:
            if req.importance > 0.8:
                focus_areas.append(req.requirement)
        
        return focus_areas[:8]  # Limit to top 8 focus areas
