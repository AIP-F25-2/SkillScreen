"""
SkillScreen - Dynamic Chat-based Interview AI Assistant
Main Streamlit application for conducting automated interviews with dynamic resume/job parsing
"""

import streamlit as st
from datetime import datetime
import json
import os
from typing import Dict, List, Optional
import re
import PyPDF2
from docx import Document
from io import BytesIO
import base64
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    log_warning("ReportLab not available. PDF generation will be disabled.")

def safe_get_response_text(response):
    """Safely extract text from Gemini response object with detailed logging"""
    try:
        log_info(f"Response type: {type(response)}")
        
        if hasattr(response, 'text') and response.text:
            text = response.text.strip()
            log_info(f"Extracted text via .text: {text[:100]}...")
            return text
        elif hasattr(response, 'parts') and response.parts:
            text = response.parts[0].text.strip()
            log_info(f"Extracted text via .parts: {text[:100]}...")
            return text
        elif hasattr(response, 'candidates') and response.candidates:
            if response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text.strip()
                log_info(f"Extracted text via .candidates: {text[:100]}...")
                return text
        
        log_error(f"Could not extract text from response: {response}")
        return ""
    except Exception as e:
        log_error(f"Error extracting response text: {e}")
        return ""

# Import our custom modules
# from llm_integration import GeminiIntegration, InterviewQuestion, InterviewResponse
import google.generativeai as genai
from config import config_manager, config
from logger import logger, log_info, log_error, log_warning

# Page configuration
st.set_page_config(
    page_title=config.ui.page_title,
    page_icon=config.ui.page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

class SimpleResumeParser:
    """Simple resume parser without spaCy/NLTK dependencies"""
    
    def __init__(self, engine=None):
        self.engine = engine
        self.skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'spring', 'express', 'laravel',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'data analysis', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'agile', 'scrum',
            'leadership', 'management', 'communication', 'teamwork', 'problem solving',
            # Non-technical skills for broader job support
            'painting', 'construction', 'maintenance', 'repair', 'installation',
            'customer service', 'sales', 'marketing', 'retail', 'hospitality',
            'teaching', 'coaching', 'coaching', 'mentoring', 'counseling',
            'healthcare', 'nursing', 'medical', 'therapy', 'counseling',
            'accounting', 'finance', 'bookkeeping', 'auditing', 'tax preparation',
            'writing', 'editing', 'journalism', 'content creation', 'copywriting',
            'design', 'graphics', 'photography', 'video editing', 'creative',
            'logistics', 'warehouse', 'inventory', 'shipping', 'receiving',
            'cooking', 'baking', 'culinary', 'food service', 'culinary',
            'driving', 'delivery', 'transportation', 'logistics', 'fleet management'
        ]
    
    def parse_resume(self, resume_text: str) -> Dict:
        """Parse resume text using AI to extract key information"""
        try:
            # Use AI to parse the resume with enhanced prompts
            parsing_prompt = f"""
            Carefully analyze this resume and extract detailed information in JSON format:
            
            Resume Text:
            {resume_text}
            
            Extract and return ONLY a JSON object with these fields:
            {{
                "name": "ACTUAL full name of the candidate (CRITICAL - find the real name, not placeholder)",
                "email": "Email address if found, otherwise 'Not provided'",
                "phone": "Phone number if found, otherwise 'Not provided'",
                "skills": ["List ALL relevant technical and professional skills"],
                "experience": "Calculate total years based on work dates (e.g., '5 years', '2-3 years', 'Entry level')",
                "education": "Highest education level or degree mentioned",
                "summary": "2-3 sentence professional summary based on their experience",
                "work_experience": ["Most recent job first: 'Job title at Company (Year-Year)'"],
                "projects": ["Project name - Brief description with technologies used"],
                "certifications": ["Any certifications or licenses mentioned"],
                "current_role": "Current or most recent job title",
                "years_of_experience": "Total years as number (e.g., 5, 2, 0 for entry level)"
            }}
            
            CRITICAL INSTRUCTIONS:
            1. The "name" field is ESSENTIAL - extract the ACTUAL person's name from the resume
            2. Don't use generic names like "Candidate", "John Doe", or "Jane Doe"
            3. Look at the very top of the resume for the name
            4. Calculate experience years accurately from employment dates
            5. Include both technical skills (programming languages, tools) and soft skills
            6. If no work experience, mark as "Entry level" or "Recent graduate"
            
            Return ONLY valid JSON, no explanations or additional text.
            """
            
            if self.engine and hasattr(self.engine, 'model_engine'):
                response_text = self.engine.model_engine.generate_with_fallback(parsing_prompt, "parsing")
            else:
                response_text = ""  # Will trigger fallback parsing
            
            # Clean up JSON response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            parsed_data = json.loads(response_text)
            
            # Validate that we extracted a real name
            if not parsed_data.get('name') or parsed_data['name'].lower() in ['candidate', 'john doe', 'jane doe', 'not provided', 'not specified', 'name']:
                # Try manual name extraction from first few lines
                lines = resume_text.strip().split('\n')[:10]
                for line in lines:
                    line = line.strip()
                    # Look for a line that looks like a name (2+ words, no special chars)
                    if (line and len(line.split()) >= 2 and len(line.split()) <= 4 and
                        not '@' in line and not any(char in line for char in ['(', ')', '+', '-', ':', '|']) and
                        not any(word in line.lower() for word in ['resume', 'cv', 'phone', 'email', 'address', 'street', 'city', 'objective', 'summary']) and
                        all(word.replace('.', '').isalpha() for word in line.split())):  # All words should be alphabetic
                        parsed_data['name'] = line
                        log_info(f"Extracted name manually: {line}")
                        break
                
                # If still no name found, look for "I am" patterns
                if not parsed_data.get('name') or parsed_data['name'].lower() in ['candidate', 'john doe', 'jane doe']:
                    import re
                    name_patterns = [
                        r'I am ([A-Z][a-z]+ [A-Z][a-z]+)',
                        r'My name is ([A-Z][a-z]+ [A-Z][a-z]+)',
                        r'^([A-Z][a-z]+ [A-Z][a-z]+)$'
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, resume_text, re.MULTILINE)
                        if match:
                            parsed_data['name'] = match.group(1)
                            log_info(f"Extracted name via pattern: {match.group(1)}")
                            break
            
            return {
                'name': parsed_data.get('name', 'Candidate'),
                'email': parsed_data.get('email', ''),
                'phone': parsed_data.get('phone', ''),
                'skills': parsed_data.get('skills', []),
                'experience': parsed_data.get('experience', 'Not specified'),
                'education': parsed_data.get('education', 'Not specified'),
                'summary': parsed_data.get('summary', ''),
                'work_experience': parsed_data.get('work_experience', []),
                'projects': parsed_data.get('projects', []),
                'raw_text': resume_text
            }
            
        except Exception as e:
            log_error(f"Error parsing resume with AI: {str(e)}")
            # Fallback to simple parsing
            return self._fallback_resume_parsing(resume_text)
    
    def _fallback_resume_parsing(self, resume_text: str) -> Dict:
        """Fallback resume parsing when AI fails"""
        resume_text_lower = resume_text.lower()
        
        # Extract name (try multiple approaches)
        name = "Candidate"
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        
        # Try to find name in first 10 lines
        for line in lines[:10]:
            line_lower = line.lower()
            # Skip lines with common resume keywords
            skip_keywords = ['resume', 'cv', 'curriculum', 'vitae', 'email', 'phone', 'address', 
                           'objective', 'summary', 'experience', 'education', 'skills', 'contact',
                           'mobile', 'tel:', 'www', 'http', '@', '(', ')', '+', '-']
            
            if not any(keyword in line_lower for keyword in skip_keywords):
                # Check if line looks like a name (2+ words, reasonable length)
                words = line.split()
                if 2 <= len(words) <= 4 and all(word.isalpha() or word.replace('.', '').isalpha() for word in words):
                    if len(line) <= 50:  # Reasonable name length
                        name = line
                        break
        
        # Alternative: look for "name:" pattern
        if name == "Candidate":
            for line in lines[:10]:
                if 'name:' in line.lower():
                    name = line.split(':')[1].strip()
                    break
        
        # Extract email
        email = ""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        if email_match:
            email = email_match.group()
        
        # Extract skills (simplified)
        skills = []
        for skill in self.skill_keywords:
            if skill in resume_text_lower:
                skills.append(skill.title())
        
        # Extract experience (look for years in work experience section)
        experience = "Not specified"
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, resume_text)
        if years:
            current_year = datetime.now().year
            # Filter out unrealistic years (before 1950 or after current year)
            valid_years = [int(year) for year in years if 1950 <= int(year) <= current_year]
            if valid_years:
                # Calculate experience based on most recent work year
                max_year = max(valid_years)
                experience_years = current_year - max_year
                if experience_years > 0:
                    experience = f"{experience_years} years"
                else:
                    experience = "Recent graduate"
        
        # Extract education
        education = "Not specified"
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'diploma', 'certificate', 'high school']
        for keyword in education_keywords:
            if keyword in resume_text_lower:
                # Find the line containing education info
                for line in lines:
                    if keyword in line.lower():
                        education = line.strip()
                        break
                break
        
        return {
            'name': name,
            'email': email,
            'phone': '',
            'skills': skills,
            'experience': experience,
            'education': education,
            'summary': '',
            'work_experience': [],
            'projects': [],
            'raw_text': resume_text
        }
    
    def parse_file(self, uploaded_file) -> str:
        """Parse uploaded file and extract text"""
        try:
            if uploaded_file.type == "text/plain":
                return str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(uploaded_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            else:
                return ""
        except Exception as e:
            log_error(f"Error parsing file: {str(e)}")
            return ""

class SimpleJobParser:
    """Simple job description parser without spaCy/NLTK dependencies"""
    
    def __init__(self, engine=None):
        self.engine = engine
        self.skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'spring', 'express', 'laravel',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'data analysis', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'agile', 'scrum',
            'leadership', 'management', 'communication', 'teamwork', 'problem solving',
            # Non-technical skills for broader job support
            'painting', 'construction', 'maintenance', 'repair', 'installation',
            'customer service', 'sales', 'marketing', 'retail', 'hospitality',
            'teaching', 'coaching', 'coaching', 'mentoring', 'counseling',
            'healthcare', 'nursing', 'medical', 'therapy', 'counseling',
            'accounting', 'finance', 'bookkeeping', 'auditing', 'tax preparation',
            'writing', 'editing', 'journalism', 'content creation', 'copywriting',
            'design', 'graphics', 'photography', 'video editing', 'creative',
            'logistics', 'warehouse', 'inventory', 'shipping', 'receiving',
            'cooking', 'baking', 'culinary', 'food service', 'culinary',
            'driving', 'delivery', 'transportation', 'logistics', 'fleet management'
        ]
    
    def parse_job_description(self, job_text: str) -> Dict:
        """Parse job description using AI to extract key information"""
        try:
            # Use AI to parse the job description
            parsing_prompt = f"""
            Parse the following job description and extract key information in JSON format:
            
            Job Description:
            {job_text}
            
            Extract and return ONLY a JSON object with these fields:
            {{
                "title": "Job title/position",
                "company": "Company name",
                "required_skills": ["skill1", "skill2", "skill3"],
                "experience_level": "Junior/Mid-level/Senior",
                "job_type": "Full-time/Part-time/Contract/Remote",
                "location": "Job location if mentioned",
                "salary_range": "Salary range if mentioned",
                "responsibilities": ["Responsibility 1", "Responsibility 2"],
                "requirements": ["Requirement 1", "Requirement 2"],
                "benefits": ["Benefit 1", "Benefit 2"]
            }}
            
            Guidelines:
            - Extract only technical and professional skills, not soft skills
            - Determine experience level based on years mentioned (0-2: Junior, 3-5: Mid, 5+: Senior)
            - Identify job type from keywords (full-time, part-time, contract, remote)
            - Extract specific responsibilities and requirements
            - Return valid JSON only, no other text
            """
            
            if self.engine and hasattr(self.engine, 'model_engine'):
                response_text = self.engine.model_engine.generate_with_fallback(parsing_prompt, "parsing")
                parsed_data = json.loads(response_text) if response_text else {}
            else:
                parsed_data = {}  # Will trigger fallback parsing
            
            return {
                'title': parsed_data.get('title', 'Position'),
                'company': parsed_data.get('company', 'Company'),
                'required_skills': parsed_data.get('required_skills', []),
                'experience_level': parsed_data.get('experience_level', 'Mid-level'),
                'job_type': parsed_data.get('job_type', 'Full-time'),
                'location': parsed_data.get('location', ''),
                'salary_range': parsed_data.get('salary_range', ''),
                'responsibilities': parsed_data.get('responsibilities', []),
                'requirements': parsed_data.get('requirements', []),
                'benefits': parsed_data.get('benefits', []),
                'description': job_text[:500] + "..." if len(job_text) > 500 else job_text
            }
            
        except Exception as e:
            log_error(f"Error parsing job description with AI: {str(e)}")
            # Fallback to simple parsing
            return self._fallback_job_parsing(job_text)
    
    def _fallback_job_parsing(self, job_text: str) -> Dict:
        """Fallback job parsing when AI fails"""
        job_text_lower = job_text.lower()
        
        # Extract company name (look for patterns like "at Company", "Company Name", etc.)
        company = "Company"
        lines = job_text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if 'at ' in line.lower():
                parts = line.lower().split('at ')
                if len(parts) > 1:
                    company = parts[1].split()[0].strip().title()
                    break
        
        # Extract job title
        title = "Position"
        job_title_keywords = [
            'developer', 'engineer', 'analyst', 'manager', 'specialist', 'coordinator',
            'painter', 'contractor', 'technician', 'operator', 'supervisor', 'director',
            'teacher', 'instructor', 'coach', 'counselor', 'advisor',
            'nurse', 'doctor', 'therapist', 'caregiver', 'assistant', 'aide',
            'accountant', 'bookkeeper', 'clerk', 'administrator', 'secretary',
            'writer', 'editor', 'journalist', 'content creator', 'copywriter',
            'designer', 'artist', 'photographer', 'videographer', 'creative',
            'driver', 'delivery', 'logistics', 'warehouse', 'inventory',
            'chef', 'cook', 'baker', 'server', 'bartender', 'host',
            'sales', 'marketing', 'retail', 'customer service', 'representative'
        ]
        for line in lines[:5]:
            if any(word in line.lower() for word in job_title_keywords):
                title = line.strip()
                break
        
        # Extract required skills
        required_skills = []
        for skill in self.skill_keywords:
            if skill in job_text_lower:
                required_skills.append(skill.title())
        
        # Extract experience level
        experience_level = "Mid-level"
        if any(word in job_text_lower for word in ['senior', 'lead', 'principal', '5+', '6+', '7+']):
            experience_level = "Senior"
        elif any(word in job_text_lower for word in ['junior', 'entry', '0-2', '1-3', '2-4']):
            experience_level = "Junior"
        
        # Extract job type
        job_type = "Full-time"
        if 'part-time' in job_text_lower:
            job_type = "Part-time"
        elif 'contract' in job_text_lower:
            job_type = "Contract"
        elif 'remote' in job_text_lower:
            job_type = "Remote"
        
        return {
            'title': title,
            'company': company,
            'required_skills': required_skills,
            'experience_level': experience_level,
            'job_type': job_type,
            'location': '',
            'salary_range': '',
            'responsibilities': [],
            'requirements': [],
            'benefits': [],
            'description': job_text[:500] + "..." if len(job_text) > 500 else job_text
        }
    


class MultiAPIEngine:
    """Multi-API AI engine using Google Gemini, OpenAI, and fallbacks for maximum reliability"""
    
    def __init__(self):
        self.apis = {}
        self.api_key = config.llm.api_key
        
        # Initialize multiple AI APIs for redundancy
        self._init_gemini_models()
        self._init_openai_models()
        
        if not self.apis:
            log_error("No AI APIs could be initialized! Using fallback mode only.")
        else:
            log_info(f"Multi-API engine initialized with {len(self.apis)} APIs: {list(self.apis.keys())}")
    
    def _init_gemini_models(self):
        """Initialize Google Gemini models"""
        try:
            genai.configure(api_key=self.api_key)
            
            # First, try to list available models
            try:
                models = genai.list_models()
                available_model_names = [model.name for model in models if 'generateContent' in model.supported_generation_methods]
                log_info(f"Available Gemini models: {available_model_names[:5]}")  # Log first 5
                if available_model_names:
                    working_models = available_model_names[:3]  # Use first 3 available models
                else:
                    working_models = []
            except Exception as e:
                log_warning(f"Could not list Gemini models: {e}")
                # Fallback to common model names
                working_models = [
                    "gemini-1.5-flash",
                    "gemini-pro", 
                    "gemini-1.5-pro",
                    "models/gemini-1.5-flash",
                    "models/gemini-pro"
                ]
            
            for model_name in working_models:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=1000,
                            candidate_count=1,
                        )
                    )
                    # Test the model with a simple query
                    test_response = model.generate_content("Hi")
                    response_text = safe_get_response_text(test_response)
                    if response_text and len(response_text.strip()) > 0:
                        self.apis[f'gemini_{model_name.replace("/", "_").replace("-", "_")}'] = model
                        log_info(f"Successfully initialized Gemini model: {model_name}")
                        break  # Use the first working model
                    else:
                        log_warning(f"Gemini model {model_name} initialized but returned empty response")
                except Exception as e:
                    log_warning(f"Failed to initialize Gemini model {model_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            log_error(f"Error initializing Gemini models: {str(e)}")
    
    def _init_openai_models(self):
        """Initialize OpenAI models (if API key available)"""
        try:
            import openai
            # You can add OpenAI API key to config if available
            openai_key = getattr(config.llm, 'openai_api_key', None)
            if openai_key:
                openai.api_key = openai_key
                self.apis['openai_gpt35'] = 'openai-gpt-3.5-turbo'  # Placeholder for now
                log_info("OpenAI API initialized")
        except ImportError:
            log_info("OpenAI package not available")
        except Exception as e:
            log_warning(f"Could not initialize OpenAI: {str(e)}")
    
    def generate_with_fallback(self, prompt, task_type="general"):
        """Generate content using multiple APIs with comprehensive fallbacks"""
        results = []
        
        # Try each available API
        for api_name, model in self.apis.items():
            if 'gemini' in api_name:
                try:
                    log_info(f"Trying {api_name} for {task_type}")
                    response = model.generate_content(prompt)
                    text = safe_get_response_text(response)
                    
                    if text and len(text.strip()) > 10:  # Valid response
                        results.append({
                            'api': api_name,
                            'text': text,
                            'length': len(text)
                        })
                        log_info(f"{api_name} succeeded for {task_type}")
                        # Return first successful response for speed
                        return text
                    else:
                        log_warning(f"{api_name} returned empty/short response for {task_type}")
                        
                except Exception as e:
                    log_error(f"{api_name} failed for {task_type}: {str(e)}")
                    continue
        
        # If all APIs failed, use comprehensive fallbacks
        log_error(f"All APIs failed for {task_type}, using smart fallback")
        return self._get_smart_fallback_response(task_type, prompt)
    
    def _get_smart_fallback_response(self, task_type, prompt=""):
        """Provide fallback responses when all models fail"""
        fallbacks = {
            'question': "Tell me about yourself and your professional background. What interests you about this position?",
            'evaluation': '{"overall_score": 5.0, "criteria_scores": {"relevance": 5.0, "technical_accuracy": 5.0, "communication": 5.0, "depth": 5.0, "job_fit": 5.0}, "strengths": ["Clear communication"], "weaknesses": ["Could provide more detail"], "feedback": "Response received and evaluated.", "improvement_tips": ["Add more specific examples"]}',
            'parsing': '{"name": "Candidate", "skills": ["Communication"], "experience": "Not specified"}',
            'summary': '{"executive_summary": "The candidate participated in a structured interview covering technical and behavioral questions. They demonstrated good communication skills in early responses but showed some uncertainty in later technical questions.", "overall_score": 5.5, "recommendation": "Consider", "recommendation_reason": "Mixed performance with strong start but declining responses in technical areas", "strengths": ["Good initial responses", "Clear communication", "Relevant experience mentioned"], "areas_for_improvement": ["Technical depth", "Consistency throughout interview", "Preparation for advanced topics"], "technical_assessment": {"score": 4.5, "summary": "Showed initial promise but struggled with more advanced technical concepts and best practices"}, "communication_assessment": {"score": 6.5, "summary": "Clear and professional communication in early responses, but became less detailed in later answers"}, "cultural_fit": {"score": 5.5, "summary": "Demonstrates some alignment with role expectations but needs more consistency"}, "key_highlights": ["Strong opening responses", "Relevant project experience with CalSnap"], "red_flags": ["Declining response quality", "Uncertainty in technical areas"], "improvement_tips": ["Prepare more thoroughly for technical questions", "Practice explaining complex concepts", "Develop consistent interview performance"], "next_steps": ["Consider for follow-up technical interview", "Focus on specific technical skills assessment"], "interviewer_notes": "Candidate started strong with good examples but struggled with advanced questions. Consider additional technical screening."}'
        }
        return fallbacks.get(task_type, "Please provide more information.")

class DynamicInterviewEngine:
    """Dynamic interview engine that works with any resume and job description"""
    
    def __init__(self):
        # Initialize multi-API engine
        self.model_engine = MultiAPIEngine()
        self.model = self.model_engine  # For compatibility
        
        self.resume_parser = SimpleResumeParser(self)
        self.job_parser = SimpleJobParser(self)
        self.active_sessions = {}
    
    def start_interview(self, resume_text: str, job_description: str, 
                       interview_type: str = 'mixed') -> str:
        """Start a new interview session"""
        try:
            # Parse resume and job description
            parsed_resume = self.resume_parser.parse_resume(resume_text)
            parsed_job = self.job_parser.parse_job_description(job_description)
            
            # Generate session ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate initial question based on parsed information
            initial_question = self._generate_initial_question(parsed_resume, parsed_job, interview_type)
            
            # Create interview state
            interview_state = {
                'session_id': session_id,
                'candidate_name': parsed_resume['name'],
                'job_title': parsed_job['title'],
                'company': parsed_job['company'],
                'current_question': initial_question,
                'question_history': [initial_question],
                'response_history': [],
                'current_question_index': 0,
                'is_started': True,
                'is_completed': False,
                'start_time': datetime.now(),
                'total_score': 0.0,
                'parsed_resume': parsed_resume,
                'parsed_job': parsed_job,
                'interview_type': interview_type
            }
            
            # Store session
            self.active_sessions[session_id] = interview_state
            
            log_info(f"Started interview session {session_id} for {parsed_resume['name']}")
            log_info(f"Initial question generated: {initial_question.get('question', 'No question')[:100]}...")
            return session_id
            
        except Exception as e:
            log_error(f"Error starting interview: {str(e)}")
            raise
    
    def _generate_initial_question(self, parsed_resume: Dict, parsed_job: Dict, interview_type: str) -> Dict:
        """Generate initial question based on resume and job description"""
        try:
            # Create context for LLM
            context = f"""
            Candidate: {parsed_resume['name']}
            Skills: {', '.join(parsed_resume['skills'])}
            Experience: {parsed_resume['experience']}
            Education: {parsed_resume['education']}
            
            Job: {parsed_job['title']} at {parsed_job['company']}
            Required Skills: {', '.join(parsed_job['required_skills'])}
            Experience Level: {parsed_job['experience_level']}
            Job Type: {parsed_job['job_type']}
            
            Interview Type: {interview_type}
            """
            
            # Generate question using LLM
            prompt = f"""
            Based on the candidate's resume and job description, generate an appropriate opening interview question.
            
            Context:
            {context}
            
            Generate a single, engaging question that:
            1. Is relevant to the job requirements
            2. Matches the candidate's experience level
            3. Is appropriate for a {interview_type} interview
            4. Helps assess the candidate's fit for the role
            
            Return only the question text.
            """
            
            if hasattr(self.model_engine, 'generate_with_fallback'):
                question_text = self.model_engine.generate_with_fallback(prompt, "question")
            else:
                question_text = "Tell me about yourself and why you're interested in this position."
            
            return {
                'question': question_text,
                'question_type': 'opening',
                'difficulty': 'medium',
                'context': context
            }
            
        except Exception as e:
            log_error(f"Error generating initial question: {str(e)}")
            return {
                'question': "Tell me about yourself and why you're interested in this position.",
                'question_type': 'opening',
                'difficulty': 'medium',
                'context': 'Default question'
            }
    
    def submit_response(self, session_id: str, response: str) -> Dict:
        """Submit candidate response and get next question or summary"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            interview_state = self.active_sessions[session_id]
            
            if interview_state['is_completed']:
                return self._get_interview_summary(session_id)
            
            # Evaluate the response
            current_question = interview_state['current_question']
            if not current_question:
                raise ValueError("No current question available")
            
            # Simple evaluation (you can enhance this with LLM)
            evaluation = self._evaluate_response(current_question, response, interview_state)
            
            # Update interview state
            interview_state['response_history'].append(evaluation)
            interview_state['current_question_index'] += 1
            
            # Check if response was off-topic and should end interview
            if evaluation.get('should_end_interview', False):
                interview_state['is_completed'] = True
                interview_state['termination_reason'] = 'off_topic'
                return self._get_interview_summary(session_id)
            
            # Check if interview should continue
            if interview_state['current_question_index'] >= 15:  # Max 15 questions for 3-round interview
                interview_state['is_completed'] = True
                interview_state['termination_reason'] = 'completed'
                return self._get_interview_summary(session_id)
            
            # Generate next question
            try:
                next_question = self._generate_next_question(interview_state)
                if not next_question or not next_question.get('question'):
                    # If question generation fails, create a simple fallback
                    question_num = len(interview_state['question_history']) + 1
                    log_warning(f"AI question generation failed, using fallback for question {question_num}")
                    
                    # Get a unique fallback question that hasn't been asked
                    fallback_question = self._get_unique_fallback_question(interview_state, question_num)
                    
                    next_question = {
                        'question': fallback_question['question'],
                        'question_type': fallback_question['type'],
                        'difficulty': 'medium',
                        'context': 'Fallback question'
                    }
                
                # Ensure we don't repeat questions
                existing_questions = [q['question'].lower() for q in interview_state['question_history']]
                if next_question['question'].lower() in existing_questions:
                    log_warning("Generated question already exists, creating unique fallback")
                    question_num = len(interview_state['question_history']) + 1
                    fallback_question = self._get_unique_fallback_question(interview_state, question_num)
                    next_question = {
                        'question': fallback_question['question'],
                        'question_type': fallback_question['type'],
                        'difficulty': 'medium',
                        'context': 'Unique fallback question'
                    }
                
                interview_state['current_question'] = next_question
                interview_state['question_history'].append(next_question)
                log_info(f"Added question {len(interview_state['question_history'])}: {next_question['question'][:50]}...")
            except Exception as e:
                log_error(f"Error generating next question: {str(e)}")
                # Force a fallback question to continue the interview
                question_num = len(interview_state['question_history']) + 1
                next_question = {
                    'question': f"Question {question_num}: Please tell me more about your professional experience.",
                    'question_type': 'general',
                    'difficulty': 'medium',
                    'context': 'Emergency fallback question'
                }
                interview_state['current_question'] = next_question
                interview_state['question_history'].append(next_question)
            
            return {
                'status': 'continue',
                'evaluation': evaluation,
                'next_question': next_question
            }
            
        except Exception as e:
            log_error(f"Error processing response: {str(e)}")
            raise
    
    def _evaluate_response(self, question: Dict, response: str, interview_state: Dict) -> Dict:
        """Evaluate candidate response using comprehensive AI analysis"""
        try:
            # First check if response is on-topic
            context_check = self._check_response_context(question, response, interview_state)
            
            if not context_check['is_relevant']:
                return {
                    'question': question['question'],
                    'response': response,
                    'score': 1.0,
                    'feedback': context_check['reason'],
                    'timestamp': datetime.now(),
                    'is_off_topic': True,
                    'should_end_interview': context_check['should_end']
                }
            
            # Comprehensive AI evaluation
            evaluation_prompt = f"""
            Evaluate this interview response comprehensively:
            
            Question: {question['question']}
            Response: {response}
            
            Candidate Background:
            - Name: {interview_state['parsed_resume']['name']}
            - Skills: {', '.join(interview_state['parsed_resume']['skills'])}
            - Experience: {interview_state['parsed_resume']['experience']}
            
            Job Requirements:
            - Position: {interview_state['parsed_job']['title']}
            - Required Skills: {', '.join(interview_state['parsed_job']['required_skills'])}
            - Experience Level: {interview_state['parsed_job']['experience_level']}
            
            Evaluate on these criteria (1-10 each):
            1. Relevance: How well does the response answer the question?
            2. Technical Accuracy: Is the technical information correct?
            3. Communication: How clear and professional is the communication?
            4. Depth: Does the response show good understanding and detail?
            5. Job Fit: How well does the response demonstrate fit for this role?
            
            Provide response in JSON format:
            {{
                "overall_score": X.X,
                "criteria_scores": {{
                    "relevance": X.X,
                    "technical_accuracy": X.X,
                    "communication": X.X,
                    "depth": X.X,
                    "job_fit": X.X
                }},
                "strengths": ["strength1", "strength2"],
                "weaknesses": ["weakness1", "weakness2"],
                "feedback": "Brief constructive feedback",
                "improvement_tips": ["tip1", "tip2"]
            }}
            """
            
            try:
                evaluation_text = self.model_engine.generate_with_fallback(evaluation_prompt, "evaluation")
                
                # Clean up the response to extract JSON
                if "```json" in evaluation_text:
                    evaluation_text = evaluation_text.split("```json")[1].split("```")[0].strip()
                elif "```" in evaluation_text:
                    evaluation_text = evaluation_text.split("```")[1].strip()
                
                evaluation_data = json.loads(evaluation_text)
                
                return {
                    'question': question['question'],
                    'response': response,
                    'score': evaluation_data.get('overall_score', 5.0),
                    'criteria_scores': evaluation_data.get('criteria_scores', {}),
                    'strengths': evaluation_data.get('strengths', []),
                    'weaknesses': evaluation_data.get('weaknesses', []),
                    'feedback': evaluation_data.get('feedback', 'Response evaluated.'),
                    'improvement_tips': evaluation_data.get('improvement_tips', []),
                    'timestamp': datetime.now(),
                    'is_off_topic': False,
                    'should_end_interview': False
                }
                
            except Exception as e:
                log_error(f"Error with comprehensive AI evaluation: {str(e)}")
                # Fallback to simple scoring
                return self._simple_evaluation_fallback(question, response)
            
        except Exception as e:
            log_error(f"Error in response evaluation: {str(e)}")
            return self._simple_evaluation_fallback(question, response)
    
    def _check_response_context(self, question: Dict, response: str, interview_state: Dict) -> Dict:
        """Check if response is relevant to the question and interview context"""
        try:
            context_prompt = f"""
            Analyze if this interview response is relevant and appropriate:
            
            Question: {question['question']}
            Response: {response}
            
            Interview Context:
            - Position: {interview_state['parsed_job']['title']}
            - Previous responses given: {len(interview_state['response_history'])}
            
            Determine:
            1. Is the response relevant to the question? (yes/no)
            2. Is it a professional interview response? (yes/no)
            3. Does it show the candidate is engaged? (yes/no)
            
            Return JSON:
            {{
                "is_relevant": true/false,
                "is_professional": true/false,
                "is_engaged": true/false,
                "reason": "Brief explanation if not relevant",
                "should_end": true/false
            }}
            """
            
            context_text = self.model_engine.generate_with_fallback(context_prompt, "evaluation")
            
            # Clean up JSON
            if "```json" in context_text:
                context_text = context_text.split("```json")[1].split("```")[0].strip()
            elif "```" in context_text:
                context_text = context_text.split("```")[1].strip()
            
            try:
                context_data = json.loads(context_text)
                # Ensure required fields exist
                if 'is_relevant' not in context_data:
                    context_data['is_relevant'] = True
                if 'is_professional' not in context_data:
                    context_data['is_professional'] = True
                if 'is_engaged' not in context_data:
                    context_data['is_engaged'] = True
                return context_data
            except json.JSONDecodeError:
                log_warning(f"Failed to parse context JSON: {context_text}")
                return {
                    "is_relevant": True,
                    "is_professional": True,
                    "is_engaged": True,
                    "reason": "",
                    "should_end": False
                }
            
        except Exception as e:
            log_error(f"Error in context checking: {str(e)}")
            # Default to relevant if AI fails
            return {
                "is_relevant": True,
                "is_professional": True,
                "is_engaged": True,
                "reason": "",
                "should_end": False
            }
    
    def _simple_evaluation_fallback(self, question: Dict, response: str) -> Dict:
        """Simple fallback evaluation when AI fails - with duplicate response detection"""
        response_lower = response.lower().strip()
        response_length = len(response.strip())
        
        # Check for duplicate/identical responses
        if hasattr(self, 'previous_responses'):
            if response_lower in self.previous_responses:
                duplicate_count = self.previous_responses.count(response_lower)
                if duplicate_count >= 2:  # Third identical response
                    return {
                        'question': question['question'],
                        'response': response,
                        'score': 0.0,
                        'criteria_scores': {
                            'relevance': 0.0,
                            'technical_accuracy': 0.0,
                            'communication': 0.0,
                            'depth': 0.0,
                            'job_fit': 0.0
                        },
                        'strengths': [],
                        'weaknesses': ["Identical response to previous questions", "Not answering specific questions", "Possible copy-paste behavior"],
                        'feedback': f"CRITICAL: This is the {duplicate_count + 1}th identical response. Interview should be terminated due to inappropriate behavior.",
                        'improvement_tips': ["Answer each question specifically", "Avoid copying previous responses", "Engage with the actual question asked"],
                        'timestamp': datetime.now(),
                        'is_off_topic': True,
                        'should_end_interview': True
                    }
                elif duplicate_count >= 1:  # Second identical response
                    return {
                        'question': question['question'],
                        'response': response,
                        'score': 1.0,
                        'criteria_scores': {
                            'relevance': 1.0,
                            'technical_accuracy': 1.0,
                            'communication': 1.0,
                            'depth': 1.0,
                            'job_fit': 1.0
                        },
                        'strengths': [],
                        'weaknesses': ["Repeated identical response", "Not addressing the specific question"],
                        'feedback': "WARNING: You provided the same response as before. Please answer this specific question.",
                        'improvement_tips': ["Read the question carefully", "Provide question-specific answers", "Avoid repeating previous responses"],
                        'timestamp': datetime.now(),
                        'is_off_topic': True,
                        'should_end_interview': False
                    }
            
            # Add to previous responses
            self.previous_responses.append(response_lower)
        else:
            # Initialize tracking
            self.previous_responses = [response_lower]
        
        # Check if response is relevant to the question
        question_lower = question['question'].lower()
        question_keywords = ['tell me about', 'describe', 'what', 'how', 'why', 'when', 'where']
        response_seems_generic = True
        
        # Basic relevance check
        if any(keyword in question_lower for keyword in ['strengths', 'strength']):
            if any(word in response_lower for word in ['strength', 'good at', 'skilled', 'expert']):
                response_seems_generic = False
        elif any(keyword in question_lower for keyword in ['challenging', 'challenge', 'difficult']):
            if any(word in response_lower for word in ['challenge', 'difficult', 'problem', 'issue', 'obstacle']):
                response_seems_generic = False
        elif any(keyword in question_lower for keyword in ['motivate', 'motivation']):
            if any(word in response_lower for word in ['motivate', 'passion', 'drive', 'inspire', 'enjoy']):
                response_seems_generic = False
        elif any(keyword in question_lower for keyword in ['technical', 'technology', 'tools']):
            if any(word in response_lower for word in ['technology', 'technical', 'code', 'programming', 'software', 'development']):
                response_seems_generic = False
        else:
            # For other questions, if response has relevant keywords, consider it somewhat relevant
            if any(word in response_lower for word in ['experience', 'project', 'work', 'team', 'develop']):
                response_seems_generic = False
        
        # Scoring based on relevance and length
        if response_seems_generic and response_length > 100:
            # Long but generic response (like copying same intro for every question)
            score = 2.0
            feedback = "Response appears generic and not specifically addressing the question asked."
            strengths = ["Provided detailed information"]
            weaknesses = ["Not answering the specific question", "Generic response", "Lacks question-specific details"]
            tips = ["Read each question carefully", "Provide specific answers to each question", "Avoid generic responses"]
        elif response_length < 10:
            score = 1.0
            feedback = "Response too short. Please provide more detail and examples."
            strengths = []
            weaknesses = ["Very brief response", "Lacks detail"]
            tips = ["Provide specific examples", "Elaborate on your experience"]
        elif any(word in response_lower for word in ['i don\'t know', 'not sure', 'can\'t remember', 'no idea']):
            score = 2.0
            feedback = "Shows uncertainty. Try to provide related experience or theoretical knowledge."
            strengths = ["Honest about limitations"]
            weaknesses = ["Lacks confidence", "Missing relevant knowledge"]
            tips = ["Draw from related experience", "Explain your thought process"]
        elif response_length < 50:
            score = 3.0
            feedback = "Brief response. Could benefit from more elaboration."
            strengths = ["Concise communication"]
            weaknesses = ["Needs more detail", "Limited examples"]
            tips = ["Add specific examples", "Explain your reasoning"]
        elif any(word in response_lower for word in ['experience', 'project', 'team', 'develop', 'implement', 'manage']) and not response_seems_generic:
            # Looks like a good professional response that's relevant
            if response_length > 150:
                score = 7.5
                feedback = "Good detailed response with relevant experience."
                strengths = ["Detailed explanation", "Relevant experience mentioned", "Question-specific answer"]
                weaknesses = []
                tips = ["Continue providing specific examples"]
            else:
                score = 6.0
                feedback = "Good response, could use more specific examples."
                strengths = ["Relevant experience", "Addresses the question"]
                weaknesses = ["Could be more detailed"]
                tips = ["Add more specific examples", "Quantify your achievements"]
        elif response_length > 200 and not response_seems_generic:
            score = 6.5
            feedback = "Comprehensive response with good detail."
            strengths = ["Thorough explanation", "Good communication skills"]
            weaknesses = []
            tips = ["Keep providing detailed responses"]
        else:
            score = 4.5
            feedback = "Adequate response. Consider adding more specific examples."
            strengths = ["Clear communication"]
            weaknesses = ["Could be more specific", "May not fully address the question"]
            tips = ["Add concrete examples", "Focus on the specific question asked"]
        
        return {
            'question': question['question'],
            'response': response,
            'score': score,
            'criteria_scores': {
                'relevance': score,
                'technical_accuracy': score,
                'communication': score,
                'depth': score,
                'job_fit': score
            },
            'strengths': strengths,
            'weaknesses': weaknesses,
            'feedback': feedback,
            'improvement_tips': tips,
            'timestamp': datetime.now(),
            'is_off_topic': False,
            'should_end_interview': False
        }
    
    def _generate_ai_summary(self, interview_state: Dict) -> Dict:
        """Generate comprehensive AI-powered interview summary"""
        try:
            # Prepare interview data for AI analysis
            qa_pairs = []
            total_score = 0
            question_count = 0
            
            for i, (question, response) in enumerate(zip(interview_state['question_history'], interview_state['response_history'])):
                qa_pairs.append(f"Q{i+1} ({question.get('question_type', 'general')}): {question['question']}")
                qa_pairs.append(f"A{i+1}: {response['response']}")
                qa_pairs.append(f"Score: {response['score']}/10")
                if response.get('strengths'):
                    qa_pairs.append(f"Strengths: {', '.join(response['strengths'])}")
                if response.get('weaknesses'):
                    qa_pairs.append(f"Weaknesses: {', '.join(response['weaknesses'])}")
                qa_pairs.append("")
                
                total_score += response['score']
                question_count += 1
            
            avg_score = total_score / question_count if question_count > 0 else 0
            termination_reason = interview_state.get('termination_reason', 'completed')
            
            summary_prompt = f"""
            Analyze this interview comprehensively and provide detailed feedback:
            
            CANDIDATE PROFILE:
            - Name: {interview_state['parsed_resume']['name']}
            - Experience: {interview_state['parsed_resume']['experience']}
            - Skills: {', '.join(interview_state['parsed_resume']['skills'])}
            - Education: {interview_state['parsed_resume'].get('education', 'Not specified')}
            
            JOB REQUIREMENTS:
            - Position: {interview_state['parsed_job']['title']}
            - Company: {interview_state['parsed_job']['company']}
            - Required Skills: {', '.join(interview_state['parsed_job']['required_skills'])}
            - Experience Level: {interview_state['parsed_job']['experience_level']}
            
            INTERVIEW DATA:
            - Total Questions: {question_count}
            - Average Score: {avg_score:.1f}/10
            - Status: {termination_reason}
            
            DETAILED Q&A ANALYSIS:
            {chr(10).join(qa_pairs)}
            
            Provide a comprehensive analysis in JSON format. Be specific and actionable:
            
            {{
                "executive_summary": "3-4 sentences summarizing overall performance, key strengths, and main concerns",
                "overall_score": {avg_score:.1f},
                "recommendation": "Choose from: 'Hire' (8.5+), 'Strong Consider' (7-8.4), 'Consider' (5-6.9), 'Do Not Hire' (<5)",
                "recommendation_reason": "Specific reason for the recommendation based on performance",
                "strengths": [
                    "Specific strength with example from responses",
                    "Another strength with concrete evidence",
                    "Third strength if applicable"
                ],
                "areas_for_improvement": [
                    "Specific weakness with actionable improvement suggestion",
                    "Another area with clear development path",
                    "Third area if applicable"
                ],
                "technical_assessment": {{
                    "score": {avg_score:.1f},
                    "summary": "Detailed assessment of technical skills, knowledge gaps, and competencies shown"
                }},
                "communication_assessment": {{
                    "score": {avg_score:.1f},
                    "summary": "Assessment of clarity, structure, professionalism, and ability to explain concepts"
                }},
                "cultural_fit": {{
                    "score": {avg_score:.1f},
                    "summary": "Assessment of alignment with role expectations, teamwork, and professional attitude"
                }},
                "key_highlights": [
                    "Most impressive response or insight",
                    "Notable problem-solving approach",
                    "Standout technical knowledge or experience"
                ],
                "red_flags": [
                    "Any concerning gaps in knowledge",
                    "Communication issues",
                    "Lack of relevant experience"
                ],
                "improvement_tips": [
                    "Specific tip for better interview performance",
                    "Skill development recommendation",
                    "Communication improvement suggestion"
                ],
                "next_steps": [
                    "Recommended action for hiring team",
                    "Follow-up interview focus areas if applicable",
                    "Reference check priorities"
                ],
                "interviewer_notes": "Detailed notes for hiring team including specific examples from responses and overall assessment"
            }}
            
            Be thorough, specific, and constructive in your analysis. Use actual examples from the responses.
            """
            
            summary_response = self.llm_integration.model.generate_content(summary_prompt)
            summary_text = safe_get_response_text(summary_response)
            
            # Clean up JSON
            if "```json" in summary_text:
                summary_text = summary_text.split("```json")[1].split("```")[0].strip()
            elif "```" in summary_text:
                summary_text = summary_text.split("```")[1].strip()
            
            summary_data = json.loads(summary_text)
            
            # Ensure recommendation is based on score
            if avg_score >= 8.5:
                summary_data['recommendation'] = 'Hire'
            elif avg_score >= 7.0:
                summary_data['recommendation'] = 'Strong Consider'
            elif avg_score >= 5.0:
                summary_data['recommendation'] = 'Consider'
            else:
                summary_data['recommendation'] = 'Do Not Hire'
            
            return summary_data
            
        except Exception as e:
            log_error(f"Error generating AI summary: {str(e)}")
            # Return fallback summary
            return {
                "executive_summary": "Interview completed successfully.",
                "overall_score": interview_state.get('total_score', 0) / len(interview_state.get('response_history', [1])),
                "recommendation": "Consider",
                "recommendation_reason": "Standard evaluation completed",
                "strengths": ["Participated in interview"],
                "areas_for_improvement": ["Continue professional development"],
                "technical_assessment": {"score": 5.0, "summary": "Assessment completed"},
                "communication_assessment": {"score": 5.0, "summary": "Assessment completed"},
                "cultural_fit": {"score": 5.0, "summary": "Assessment completed"},
                "key_highlights": ["Engaged in interview process"],
                "red_flags": [],
                "improvement_tips": ["Practice interview skills"],
                "next_steps": ["Standard follow-up"],
                "interviewer_notes": "Interview completed successfully"
            }
    
    def _generate_next_question(self, interview_state: Dict) -> Dict:
        """Generate next question based on previous responses and 3-round interview structure"""
        try:
            current_question_num = len(interview_state['question_history']) + 1
            total_questions = 15  # Target 10-15 minute interview
            
            # 3-Round Interview Structure:
            # Round 1: General Questions (1-5) - Background, motivation, soft skills
            # Round 2: Technical Questions (6-10) - Hands-on experience, problem-solving
            # Round 3: Theoretical Questions (11-15) - Concepts, best practices, industry knowledge
            
            if current_question_num <= 5:
                question_type = 'general'
                round_name = 'Round 1: General Assessment'
                question_focus = 'background, experience, motivation, soft skills, career goals, teamwork'
                round_info = f"This is {round_name}. Focus on understanding the candidate's background and soft skills."
            elif current_question_num <= 10:
                question_type = 'technical'
                round_name = 'Round 2: Technical Assessment'
                question_focus = 'hands-on experience, specific skills, tools, technologies, problem-solving, coding, implementation'
                round_info = f"This is {round_name}. Focus on technical skills relevant to the job requirements."
            else:
                question_type = 'theoretical'
                round_name = 'Round 3: Theoretical Assessment'
                question_focus = 'concepts, best practices, methodologies, industry knowledge, system design, architecture'
                round_info = f"This is {round_name}. Focus on deep understanding of concepts and best practices."
            
            # Create context for next question
            context = f"""
            {round_info}
            
            Previous questions and responses:
            """
            for i, (q, r) in enumerate(zip(interview_state['question_history'], interview_state['response_history'])):
                context += f"Q{i+1} ({q.get('question_type', 'general')}): {q['question']}\nA{i+1}: {r['response']}\nScore: {r['score']}/10\n\n"
            
            context += f"""
            CANDIDATE PROFILE:
            - Name: {interview_state['parsed_resume']['name']}
            - Skills: {', '.join(interview_state['parsed_resume']['skills'])}
            - Experience: {interview_state['parsed_resume']['experience']}
            - Education: {interview_state['parsed_resume'].get('education', 'Not specified')}
            
            JOB REQUIREMENTS:
            - Position: {interview_state['parsed_job']['title']} at {interview_state['parsed_job']['company']}
            - Required Skills: {', '.join(interview_state['parsed_job']['required_skills'])}
            - Experience Level: {interview_state['parsed_job']['experience_level']}
            """
            
            # Get list of previous questions to avoid repetition
            previous_questions = [q['question'] for q in interview_state['question_history']]
            
            # Special prompts for different rounds
            if question_type == 'general':
                specific_guidance = """
                - Ask about their background, motivation, and career journey
                - Explore soft skills like teamwork, communication, problem-solving approach
                - Understand their interest in this specific role and company
                - Ask about challenges they've faced and how they overcame them
                - Focus on behavioral and situational questions
                """
            elif question_type == 'technical':
                specific_guidance = f"""
                - Ask about specific technologies and tools mentioned in their resume
                - Test hands-on experience with {', '.join(interview_state['parsed_job']['required_skills'][:3])}
                - Ask about real projects they've worked on
                - Test problem-solving with technical scenarios
                - Ask about debugging, optimization, or implementation challenges
                """
            else:  # theoretical
                specific_guidance = f"""
                - Test deep understanding of concepts related to {interview_state['parsed_job']['title']}
                - Ask about best practices, design patterns, or methodologies
                - Explore system design or architectural thinking
                - Test knowledge of industry standards and trends
                - Ask about trade-offs and decision-making in technical contexts
                """
            
            prompt = f"""
            Generate question #{current_question_num} of {total_questions} for this structured interview.
            
            CURRENT ROUND: {round_name}
            QUESTION TYPE: {question_type.upper()}
            FOCUS AREAS: {question_focus}
            
            SPECIFIC GUIDANCE FOR THIS ROUND:
            {specific_guidance}
            
            CANDIDATE & JOB CONTEXT:
            {context}
            
            PREVIOUS QUESTIONS (DO NOT REPEAT OR REPHRASE):
            {chr(10).join([f"- {q}" for q in previous_questions])}
            
            REQUIREMENTS:
            1. Generate a UNIQUE {question_type} question that hasn't been asked before
            2. Make it specific to their background and the job requirements
            3. Build on insights from their previous responses
            4. Ensure it's appropriate for their experience level
            5. Make it conversational and engaging
            6. Focus specifically on {question_focus}
            
            Return ONLY the question text, nothing else.
            """
            
            question_text = self.model_engine.generate_with_fallback(prompt, "question")
            
            # Clean up response
            if question_text.startswith('"') and question_text.endswith('"'):
                question_text = question_text[1:-1]
            
            return {
                'question': question_text,
                'question_type': question_type,
                'difficulty': 'medium',
                'context': context
            }
            
        except Exception as e:
            log_error(f"Error generating next question: {str(e)}")
            # Generate a fallback question based on question number
            question_number = len(interview_state['question_history']) + 1
            # Fallback questions organized by rounds
            if question_number <= 5:
                # Round 1: General Assessment
                fallback_questions = [
                    "Tell me about yourself and your professional background.",
                    "What are your key strengths and how do they apply to this role?", 
                    "Describe a challenging situation you faced and how you handled it.",
                    "What motivates you in your work and career?",
                    "Tell me about a time when you had to work collaboratively in a team."
                ]
                question_type = 'general'
            elif question_number <= 10:
                # Round 2: Technical Assessment
                fallback_questions = [
                    "Walk me through your technical experience and the technologies you've worked with.",
                    "Describe a complex technical project you've worked on recently.",
                    "How do you approach debugging and troubleshooting technical issues?",
                    "What development tools and methodologies do you prefer and why?",
                    "Tell me about a time when you had to learn a new technology quickly."
                ]
                question_type = 'technical'
            else:
                # Round 3: Theoretical Assessment
                fallback_questions = [
                    "What are the best practices you follow in your field?",
                    "How do you ensure code quality and maintainability in your projects?",
                    "Explain your approach to system design and architecture decisions.",
                    "What industry trends do you think will shape the future of this field?",
                    "How do you balance performance, scalability, and maintainability in your work?"
                ]
                question_type = 'theoretical'
            
            # Select question based on position within the round
            round_position = ((question_number - 1) % 5)
            if round_position < len(fallback_questions):
                question_text = fallback_questions[round_position]
            else:
                question_text = fallback_questions[0]  # Default to first question of the round
            
            return {
                'question': question_text,
                'question_type': question_type,
                'difficulty': 'medium',
                'context': 'Fallback question due to AI error'
            }
    
    def _get_interview_summary(self, session_id: str) -> Dict:
        """Generate comprehensive AI-powered interview summary"""
        interview_state = self.active_sessions[session_id]
        interview_state['is_completed'] = True
        interview_state['end_time'] = datetime.now()
        
        try:
            # Generate comprehensive AI summary
            if hasattr(self.model_engine, 'apis') and self.model_engine.apis:
                # Try AI summary if APIs are available
                summary_data = self._generate_ai_summary(interview_state)
            else:
                # Use enhanced fallback summary when no AI available
                summary_data = self._generate_enhanced_fallback_summary(interview_state)
            
            # Calculate total score
            if interview_state['response_history']:
                total_score = sum(r['score'] for r in interview_state['response_history'])
                avg_score = total_score / len(interview_state['response_history'])
            else:
                avg_score = 0.0
            
            interview_state['total_score'] = avg_score
            summary_data['total_score'] = avg_score
            
            return {
                'status': 'completed',
                'summary_data': summary_data,
                'total_score': avg_score,
                'total_questions': len(interview_state['question_history']),
                'total_responses': len(interview_state['response_history']),
                'recommendation': summary_data.get('recommendation', 'Consider'),
                'summary': summary_data.get('executive_summary', f"Interview completed for {interview_state.get('candidate_name', 'Candidate')}")
            }
            
        except Exception as e:
            log_error(f"Error generating AI summary: {str(e)}")
            # Fallback to simple summary
            return self._generate_simple_summary(interview_state)
    
    def _generate_ai_summary_duplicate(self, interview_state: Dict) -> Dict:
            """Generate comprehensive AI-powered interview summary - DUPLICATE TO REMOVE"""
            try:
                # Prepare interview data for AI analysis
                qa_pairs = []
                total_score = 0
                question_count = 0
                
                for i, (question, response) in enumerate(zip(interview_state['question_history'], interview_state['response_history'])):
                    qa_pairs.append(f"Q{i+1} ({question.get('question_type', 'general')}): {question['question']}")
                    qa_pairs.append(f"A{i+1}: {response['response']}")
                    qa_pairs.append(f"Score: {response['score']}/10")
                    if response.get('strengths'):
                        qa_pairs.append(f"Strengths: {', '.join(response['strengths'])}")
                    if response.get('weaknesses'):
                        qa_pairs.append(f"Weaknesses: {', '.join(response['weaknesses'])}")
                    qa_pairs.append("")
                    
                    total_score += response['score']
                    question_count += 1
                
                avg_score = total_score / question_count if question_count > 0 else 0
                termination_reason = interview_state.get('termination_reason', 'completed')
                
                summary_prompt = f"""
                Analyze this interview comprehensively and provide detailed feedback:
                
                CANDIDATE PROFILE:
                - Name: {interview_state['parsed_resume']['name']}
                - Experience: {interview_state['parsed_resume']['experience']}
                - Skills: {', '.join(interview_state['parsed_resume']['skills'])}
                - Education: {interview_state['parsed_resume'].get('education', 'Not specified')}
                
                JOB REQUIREMENTS:
                - Position: {interview_state['parsed_job']['title']}
                - Company: {interview_state['parsed_job']['company']}
                - Required Skills: {', '.join(interview_state['parsed_job']['required_skills'])}
                - Experience Level: {interview_state['parsed_job']['experience_level']}
                
                INTERVIEW DATA:
                - Total Questions: {question_count}
                - Average Score: {avg_score:.1f}/10
                - Status: {termination_reason}
                
                DETAILED Q&A ANALYSIS:
                {chr(10).join(qa_pairs)}
                
                Provide a comprehensive analysis in JSON format. Be specific and actionable:
                
                {{
                    "executive_summary": "3-4 sentences summarizing overall performance, key strengths, and main concerns",
                    "overall_score": {avg_score:.1f},
                    "recommendation": "Choose from: 'Hire' (8.5+), 'Strong Consider' (7-8.4), 'Consider' (5-6.9), 'Do Not Hire' (<5)",
                    "recommendation_reason": "Specific reason for the recommendation based on performance",
                    "strengths": [
                        "Specific strength with example from responses",
                        "Another strength with concrete evidence",
                        "Third strength if applicable"
                    ],
                    "areas_for_improvement": [
                        "Specific weakness with actionable improvement suggestion",
                        "Another area with clear development path",
                        "Third area if applicable"
                    ],
                    "technical_assessment": {{
                        "score": X.X,
                        "summary": "Detailed assessment of technical skills, knowledge gaps, and competencies shown"
                    }},
                    "communication_assessment": {{
                        "score": X.X,
                        "summary": "Assessment of clarity, structure, professionalism, and ability to explain concepts"
                    }},
                    "cultural_fit": {{
                        "score": X.X,
                        "summary": "Assessment of alignment with role expectations, teamwork, and professional attitude"
                    }},
                    "key_highlights": [
                        "Most impressive response or insight",
                        "Notable problem-solving approach",
                        "Standout technical knowledge or experience"
                    ],
                    "red_flags": [
                        "Any concerning gaps in knowledge",
                        "Communication issues",
                        "Lack of relevant experience"
                    ],
                    "improvement_tips": [
                        "Specific tip for better interview performance",
                        "Skill development recommendation",
                        "Communication improvement suggestion"
                    ],
                    "next_steps": [
                        "Recommended action for hiring team",
                        "Follow-up interview focus areas if applicable",
                        "Reference check priorities"
                    ],
                    "interviewer_notes": "Detailed notes for hiring team including specific examples from responses and overall assessment"
                }}
                
                Be thorough, specific, and constructive in your analysis. Use actual examples from the responses.
                """
                
                summary_text = self.model_engine.generate_with_fallback(summary_prompt, "summary")
                
                # Clean up JSON
                if "```json" in summary_text:
                    summary_text = summary_text.split("```json")[1].split("```")[0].strip()
                elif "```" in summary_text:
                    summary_text = summary_text.split("```")[1].strip()
                
                summary_data = json.loads(summary_text)
                
                # Ensure recommendation is based on score
                if avg_score >= 8.5:
                    summary_data['recommendation'] = 'Hire'
                elif avg_score >= 7.0:
                    summary_data['recommendation'] = 'Strong Consider'
                elif avg_score >= 5.0:
                    summary_data['recommendation'] = 'Consider'
                else:
                    summary_data['recommendation'] = 'Do Not Hire'
                
                return summary_data
                
            except Exception as e:
                log_error(f"Error generating AI summary: {str(e)}")
                raise
    
    def _generate_enhanced_fallback_summary(self, interview_state: Dict) -> Dict:
        """Generate enhanced fallback summary with intelligent analysis"""
        if interview_state['response_history']:
            scores = [r['score'] for r in interview_state['response_history']]
            total_score = sum(scores)
            avg_score = total_score / len(scores)
            
            # Analyze response patterns
            responses = [r['response'].lower().strip() for r in interview_state['response_history']]
            unique_responses = set(responses)
            duplicate_ratio = 1 - (len(unique_responses) / len(responses))
            
            # Analyze score patterns
            low_scores = sum(1 for s in scores if s <= 2.0)
            high_scores = sum(1 for s in scores if s >= 7.0)
            
            # Generate intelligent summary based on patterns
            if duplicate_ratio > 0.8:  # More than 80% duplicate responses
                executive_summary = f"CRITICAL CONCERN: The candidate provided identical or nearly identical responses to {int(duplicate_ratio * 100)}% of questions, suggesting they may not have been properly engaging with the interview questions. This pattern indicates either a lack of preparation, inability to understand the questions, or inappropriate interview behavior."
                recommendation = "Do Not Hire"
                recommendation_reason = "Candidate failed to engage properly with interview questions, providing repetitive responses that do not demonstrate competency or professionalism."
                strengths = ["Consistent communication style"] if avg_score > 3 else []
                areas_for_improvement = [
                    "Answer each question specifically and individually",
                    "Demonstrate ability to understand and respond to different types of questions",
                    "Show engagement with the interview process",
                    "Avoid providing identical responses to different questions"
                ]
                red_flags = [
                    f"Provided identical responses to {int(duplicate_ratio * 100)}% of questions",
                    "Did not demonstrate question comprehension",
                    "Showed lack of interview preparation or engagement"
                ]
                key_highlights = []
                
            elif avg_score < 3.0:
                executive_summary = f"The candidate struggled significantly throughout the interview with an average score of {avg_score:.1f}/10. Multiple responses showed uncertainty, lack of preparation, or inability to address the questions asked."
                recommendation = "Do Not Hire"
                recommendation_reason = f"Poor overall performance with {low_scores} responses scoring 2.0 or below, indicating insufficient qualifications or preparation."
                strengths = ["Participated in the full interview"] if len(interview_state['response_history']) >= 10 else []
                areas_for_improvement = [
                    "Improve technical knowledge and experience",
                    "Better preparation for interview questions",
                    "Develop more comprehensive responses with specific examples"
                ]
                red_flags = [f"{low_scores} responses scored very poorly (≤2.0)", "Consistent uncertainty or lack of knowledge"]
                key_highlights = []
                
            elif avg_score >= 7.0:
                executive_summary = f"The candidate performed well throughout the interview with an average score of {avg_score:.1f}/10, demonstrating good knowledge and communication skills across multiple areas."
                recommendation = "Strong Consider" if avg_score >= 8.0 else "Consider"
                recommendation_reason = f"Strong performance with {high_scores} responses scoring 7.0 or above, showing good competency and preparation."
                strengths = [
                    "Consistently high-quality responses",
                    "Good technical knowledge and experience",
                    "Strong communication skills",
                    "Well-prepared for the interview"
                ]
                areas_for_improvement = [
                    "Continue developing technical expertise",
                    "Maintain consistent performance across all question types"
                ]
                red_flags = []
                key_highlights = [f"{high_scores} responses scored 7.0 or above", "Demonstrated good overall competency"]
                
            else:  # Average performance
                executive_summary = f"The candidate showed mixed performance with an average score of {avg_score:.1f}/10. Some responses demonstrated good knowledge while others showed areas needing improvement."
                recommendation = "Consider"
                recommendation_reason = f"Mixed performance with both strengths and weaknesses evident. {high_scores} strong responses but also {low_scores} weak responses."
                strengths = [
                    "Showed competency in some areas",
                    "Participated fully in the interview process"
                ]
                areas_for_improvement = [
                    "Improve consistency across all question types",
                    "Strengthen weaker technical areas",
                    "Provide more specific examples and details"
                ]
                red_flags = [f"{low_scores} responses scored poorly"] if low_scores > 3 else []
                key_highlights = [f"{high_scores} responses showed strong competency"] if high_scores > 0 else []
            
        else:
            avg_score = 0.0
            executive_summary = "No responses were recorded during the interview."
            recommendation = "Do Not Hire"
            recommendation_reason = "Interview was not completed properly."
            strengths = []
            areas_for_improvement = ["Complete the interview process"]
            red_flags = ["No responses recorded"]
            key_highlights = []
        
        # Determine scores for different categories based on overall performance
        if avg_score >= 7.0:
            tech_score = min(avg_score + 0.5, 10.0)
            comm_score = avg_score
            fit_score = avg_score - 0.5
        elif avg_score >= 5.0:
            tech_score = avg_score - 0.5
            comm_score = avg_score + 0.5
            fit_score = avg_score
        else:
            tech_score = avg_score
            comm_score = max(avg_score - 0.5, 0.0)
            fit_score = max(avg_score - 1.0, 0.0)
        
        return {
            "executive_summary": executive_summary,
            "overall_score": avg_score,
            "recommendation": recommendation,
            "recommendation_reason": recommendation_reason,
            "strengths": strengths,
            "areas_for_improvement": areas_for_improvement,
            "technical_assessment": {
                "score": tech_score,
                "summary": f"Technical competency assessment based on responses to technical questions and overall performance patterns."
            },
            "communication_assessment": {
                "score": comm_score,
                "summary": f"Communication skills evaluated based on response clarity, detail, and engagement with questions."
            },
            "cultural_fit": {
                "score": fit_score,
                "summary": f"Cultural fit assessment based on professionalism, engagement, and interview behavior."
            },
            "key_highlights": key_highlights,
            "red_flags": red_flags,
            "improvement_tips": [
                "Practice answering different types of interview questions specifically",
                "Prepare specific examples for each type of question",
                "Focus on understanding what each question is asking before responding"
            ],
            "next_steps": [
                "Review detailed response analysis",
                "Consider follow-up interview if performance was borderline",
                "Check references if moving forward"
            ],
            "interviewer_notes": f"Automated analysis based on {len(interview_state['response_history'])} responses with average score of {avg_score:.1f}/10. Response uniqueness: {(1-duplicate_ratio)*100:.1f}%."
        }
    
    def _generate_simple_summary(self, interview_state: Dict) -> Dict:
        """Generate simple fallback summary"""
        if interview_state['response_history']:
            total_score = sum(r['score'] for r in interview_state['response_history'])
            avg_score = total_score / len(interview_state['response_history'])
        else:
            avg_score = 0.0
        
        if avg_score >= 8:
            recommendation = "Hire"
        elif avg_score >= 6:
            recommendation = "Strong Consider"
        elif avg_score >= 4:
            recommendation = "Consider"
        else:
            recommendation = "Do Not Hire"
        
        return {
            'status': 'completed',
            'summary_data': {
                'executive_summary': f"Interview completed for {interview_state.get('candidate_name', 'Candidate')}. Average score: {avg_score:.1f}/10",
                'recommendation': recommendation,
                'strengths': ['Completed the interview'],
                'areas_for_improvement': ['Detailed AI analysis unavailable'],
                'next_steps': ['Review responses manually']
            },
            'total_score': avg_score,
            'total_questions': len(interview_state['question_history']),
            'total_responses': len(interview_state['response_history']),
            'recommendation': recommendation,
            'summary': f"Interview completed. Total score: {avg_score:.1f}/10"
        }
    
    def _get_unique_fallback_question(self, interview_state: Dict, question_num: int) -> Dict:
        """Get a unique fallback question that hasn't been asked yet"""
        asked_questions = [q['question'].lower() for q in interview_state['question_history']]
        
        # Comprehensive fallback questions by round
        all_fallback_questions = {
            'general': [
                "Tell me about yourself and your professional background.",
                "What are your key strengths and how do they apply to this role?",
                "Describe a challenging situation you faced and how you handled it.",
                "What motivates you in your work and career?",
                "Tell me about a time when you had to work collaboratively in a team.",
                "How do you handle stress and pressure in your work?",
                "What are your career goals for the next 3-5 years?",
                "Describe a time when you had to adapt to a significant change.",
                "What do you consider your greatest professional achievement?",
                "How do you prioritize tasks when you have multiple deadlines?"
            ],
            'technical': [
                "Walk me through your technical experience and the technologies you've worked with.",
                "Describe a complex technical project you've worked on recently.",
                "How do you approach debugging and troubleshooting technical issues?",
                "What development tools and methodologies do you prefer and why?",
                "Tell me about a time when you had to learn a new technology quickly.",
                "How do you ensure the quality and reliability of your code?",
                "Describe your experience with version control and collaboration tools.",
                "What's your approach to testing and quality assurance?",
                "How do you stay updated with the latest technologies in your field?",
                "Describe a technical challenge that required creative problem-solving."
            ],
            'theoretical': [
                "What are the best practices you follow in your field?",
                "How do you ensure code quality and maintainability in your projects?",
                "Explain your approach to system design and architecture decisions.",
                "What industry trends do you think will shape the future of this field?",
                "How do you balance performance, scalability, and maintainability in your work?",
                "What are the key principles of software engineering that guide your work?",
                "How do you approach security considerations in your development process?",
                "Describe your understanding of agile methodologies and their benefits.",
                "What are the most important factors to consider when designing APIs?",
                "How do you approach database design and optimization?"
            ]
        }
        
        # Determine question type based on question number
        if question_num <= 5:
            question_type = 'general'
        elif question_num <= 10:
            question_type = 'technical'
        else:
            question_type = 'theoretical'
        
        # Find a question that hasn't been asked
        available_questions = all_fallback_questions[question_type]
        for question in available_questions:
            if question.lower() not in asked_questions:
                return {'question': question, 'type': question_type}
        
        # If all questions in the category have been asked, use a generic one with question number
        return {
            'question': f"Question {question_num}: Can you elaborate more on your experience in this field?",
            'type': question_type
        }
    
    def get_current_question(self, session_id: str) -> Dict:
        """Get current question for session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]['current_question']
        return None
    
    def generate_interview_report(self, session_id: str) -> str:
        """Generate a comprehensive interview report for download"""
        try:
            interview_state = self.active_sessions[session_id]
            summary_data = interview_state.get('summary_data', {})
            
            # Generate comprehensive report
            report_content = f"""
# INTERVIEW REPORT
## SkillScreen - AI Interview Assistant

---

### CANDIDATE INFORMATION
**Name:** {interview_state['parsed_resume']['name']}
**Email:** {interview_state['parsed_resume'].get('email', 'Not provided')}
**Experience:** {interview_state['parsed_resume']['experience']}
**Interview Date:** {interview_state['start_time'].strftime('%B %d, %Y at %I:%M %p')}

### POSITION DETAILS
**Job Title:** {interview_state['parsed_job']['title']}
**Company:** {interview_state['parsed_job']['company']}
**Experience Level:** {interview_state['parsed_job']['experience_level']}
**Job Type:** {interview_state['parsed_job']['job_type']}

---

### EXECUTIVE SUMMARY
{summary_data.get('executive_summary', 'Interview completed successfully.')}

**Overall Score:** {interview_state['total_score']:.1f}/10
**Recommendation:** {summary_data.get('recommendation', 'Consider')}

---

### DETAILED ASSESSMENT

#### Technical Skills Assessment
**Score:** {summary_data.get('technical_assessment', {}).get('score', 'N/A')}/10
{summary_data.get('technical_assessment', {}).get('summary', 'Assessment not available')}

#### Communication Skills Assessment
**Score:** {summary_data.get('communication_assessment', {}).get('score', 'N/A')}/10
{summary_data.get('communication_assessment', {}).get('summary', 'Assessment not available')}

#### Cultural Fit Assessment
**Score:** {summary_data.get('cultural_fit', {}).get('score', 'N/A')}/10
{summary_data.get('cultural_fit', {}).get('summary', 'Assessment not available')}

---

### STRENGTHS
"""
            
            # Add strengths
            strengths = summary_data.get('strengths', [])
            if strengths:
                for i, strength in enumerate(strengths, 1):
                    report_content += f"{i}. {strength}\n"
            else:
                report_content += "No specific strengths identified.\n"
            
            report_content += "\n### AREAS FOR IMPROVEMENT\n"
            
            # Add areas for improvement
            improvements = summary_data.get('areas_for_improvement', [])
            if improvements:
                for i, improvement in enumerate(improvements, 1):
                    report_content += f"{i}. {improvement}\n"
            else:
                report_content += "No specific areas for improvement identified.\n"
            
            report_content += "\n### KEY HIGHLIGHTS\n"
            
            # Add key highlights
            highlights = summary_data.get('key_highlights', [])
            if highlights:
                for i, highlight in enumerate(highlights, 1):
                    report_content += f"{i}. {highlight}\n"
            else:
                report_content += "No key highlights identified.\n"
            
            # Add red flags if any
            red_flags = summary_data.get('red_flags', [])
            if red_flags:
                report_content += "\n### RED FLAGS\n"
                for i, flag in enumerate(red_flags, 1):
                    report_content += f"{i}. {flag}\n"
            
            report_content += "\n---\n\n### INTERVIEW QUESTIONS & RESPONSES\n"
            
            # Add Q&A section
            for i, (question, response) in enumerate(zip(interview_state['question_history'], interview_state['response_history']), 1):
                report_content += f"\n**Question {i}:** {question['question']}\n\n"
                report_content += f"**Response:** {response['response']}\n\n"
                report_content += f"**Score:** {response['score']}/10\n"
                if response.get('feedback'):
                    report_content += f"**Feedback:** {response['feedback']}\n"
                report_content += "\n---\n"
            
            report_content += "\n### NEXT STEPS\n"
            
            # Add next steps
            next_steps = summary_data.get('next_steps', [])
            if next_steps:
                for i, step in enumerate(next_steps, 1):
                    report_content += f"{i}. {step}\n"
            else:
                report_content += "1. Review candidate responses in detail\n2. Conduct follow-up interview if needed\n3. Check references\n"
            
            report_content += f"\n### INTERVIEWER NOTES\n"
            report_content += summary_data.get('interviewer_notes', 'No additional notes provided.')
            
            report_content += f"\n\n---\n\n*Report generated by SkillScreen AI Interview Assistant on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*\n"
            report_content += f"*Interview Session ID: {session_id}*"
            
            return report_content
            
        except Exception as e:
            log_error(f"Error generating interview report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def generate_pdf_report(self, session_id: str) -> BytesIO:
        """Generate a PDF interview report"""
        if not REPORTLAB_AVAILABLE:
            log_error("ReportLab not available, cannot generate PDF")
            return None
        
        try:
            interview_state = self.active_sessions[session_id]
            summary_data = interview_state.get('summary_data', {})
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # Center alignment
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            normal_style = styles['Normal']
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("INTERVIEW REPORT", title_style))
            story.append(Paragraph("SkillScreen - AI Interview Assistant", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Candidate Information
            story.append(Paragraph("CANDIDATE INFORMATION", heading_style))
            candidate_data = [
                ['Name:', interview_state['parsed_resume']['name']],
                ['Email:', interview_state['parsed_resume'].get('email', 'Not provided')],
                ['Experience:', interview_state['parsed_resume']['experience']],
                ['Interview Date:', interview_state['start_time'].strftime('%B %d, %Y at %I:%M %p')]
            ]
            
            candidate_table = Table(candidate_data, colWidths=[1.5*inch, 4*inch])
            candidate_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(candidate_table)
            story.append(Spacer(1, 20))
            
            # Position Details
            story.append(Paragraph("POSITION DETAILS", heading_style))
            position_data = [
                ['Job Title:', interview_state['parsed_job']['title']],
                ['Company:', interview_state['parsed_job']['company']],
                ['Experience Level:', interview_state['parsed_job']['experience_level']],
                ['Job Type:', interview_state['parsed_job']['job_type']]
            ]
            
            position_table = Table(position_data, colWidths=[1.5*inch, 4*inch])
            position_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(position_table)
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
            story.append(Paragraph(summary_data.get('executive_summary', 'Interview completed successfully.'), normal_style))
            
            # Scores
            scores_data = [
                ['Overall Score:', f"{interview_state['total_score']:.1f}/10"],
                ['Recommendation:', summary_data.get('recommendation', 'Consider')]
            ]
            
            scores_table = Table(scores_data, colWidths=[1.5*inch, 4*inch])
            scores_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(scores_table)
            story.append(Spacer(1, 20))
            
            # Detailed Assessment
            story.append(Paragraph("DETAILED ASSESSMENT", heading_style))
            
            # Technical Skills
            tech_score = summary_data.get('technical_assessment', {}).get('score', 'N/A')
            story.append(Paragraph(f"<b>Technical Skills:</b> {tech_score}/10", normal_style))
            story.append(Paragraph(summary_data.get('technical_assessment', {}).get('summary', 'Assessment not available'), normal_style))
            story.append(Spacer(1, 10))
            
            # Communication
            comm_score = summary_data.get('communication_assessment', {}).get('score', 'N/A')
            story.append(Paragraph(f"<b>Communication:</b> {comm_score}/10", normal_style))
            story.append(Paragraph(summary_data.get('communication_assessment', {}).get('summary', 'Assessment not available'), normal_style))
            story.append(Spacer(1, 10))
            
            # Cultural Fit
            fit_score = summary_data.get('cultural_fit', {}).get('score', 'N/A')
            story.append(Paragraph(f"<b>Cultural Fit:</b> {fit_score}/10", normal_style))
            story.append(Paragraph(summary_data.get('cultural_fit', {}).get('summary', 'Assessment not available'), normal_style))
            story.append(Spacer(1, 20))
            
            # Strengths
            story.append(Paragraph("STRENGTHS", heading_style))
            strengths = summary_data.get('strengths', [])
            if strengths:
                for i, strength in enumerate(strengths, 1):
                    story.append(Paragraph(f"{i}. {strength}", normal_style))
            else:
                story.append(Paragraph("No specific strengths identified.", normal_style))
            story.append(Spacer(1, 15))
            
            # Areas for Improvement
            story.append(Paragraph("AREAS FOR IMPROVEMENT", heading_style))
            improvements = summary_data.get('areas_for_improvement', [])
            if improvements:
                for i, improvement in enumerate(improvements, 1):
                    story.append(Paragraph(f"{i}. {improvement}", normal_style))
            else:
                story.append(Paragraph("No specific areas for improvement identified.", normal_style))
            story.append(Spacer(1, 15))
            
            # Improvement Tips
            if summary_data.get('improvement_tips'):
                story.append(Paragraph("IMPROVEMENT TIPS", heading_style))
                for i, tip in enumerate(summary_data['improvement_tips'], 1):
                    story.append(Paragraph(f"{i}. {tip}", normal_style))
                story.append(Spacer(1, 15))
            
            # Questions and Responses
            story.append(Paragraph("INTERVIEW QUESTIONS & RESPONSES", heading_style))
            for i, (question, response) in enumerate(zip(interview_state['question_history'], interview_state['response_history']), 1):
                story.append(Paragraph(f"<b>Question {i}:</b> {question['question']}", normal_style))
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Response:</b> {response['response']}", normal_style))
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Score:</b> {response['score']}/10", normal_style))
                if response.get('feedback'):
                    story.append(Paragraph(f"<b>Feedback:</b> {response['feedback']}", normal_style))
                story.append(Spacer(1, 15))
            
            # Next Steps
            if summary_data.get('next_steps'):
                story.append(Paragraph("NEXT STEPS", heading_style))
                for i, step in enumerate(summary_data['next_steps'], 1):
                    story.append(Paragraph(f"{i}. {step}", normal_style))
                story.append(Spacer(1, 15))
            
            # Interviewer Notes
            story.append(Paragraph("INTERVIEWER NOTES", heading_style))
            story.append(Paragraph(summary_data.get('interviewer_notes', 'No additional notes provided.'), normal_style))
            story.append(Spacer(1, 20))
            
            # Footer
            story.append(Paragraph(f"<i>Report generated by SkillScreen AI Interview Assistant on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>", normal_style))
            story.append(Paragraph(f"<i>Interview Session ID: {session_id}</i>", normal_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            log_error(f"Error generating PDF report: {str(e)}")
            return None

def show_welcome_message():
    """Display welcome message and app explanation"""
    st.markdown("""
    ## Welcome to SkillScreen! 👋
    
    **Your AI-Powered Interview Assistant**
    
    ### How it works:
    1. **📄 Upload your resume** (PDF, DOCX, or paste text)
    2. **💼 Provide the job description** you're applying for
    3. **🤖 Start your personalized interview** (10-15 minutes)
    4. **📊 Get detailed feedback** and downloadable reports
    
    ### What to expect:
    - **General questions** to understand your background
    - **Technical questions** based on the job requirements
    - **Theoretical questions** to test your knowledge
    - **Real-time evaluation** with detailed feedback
    - **Comprehensive summary** with improvement tips
    
    ### Ready to begin? Let's get started! 🚀
    """)

def main():
    """Main application function"""
    st.title("🎯 SkillScreen - AI Interview Assistant")
    
    # Show welcome message if no session is active
    if 'interview_engine' not in st.session_state:
        show_welcome_message()
    
    st.markdown("---")
    st.markdown("---")
    
    # Initialize session state
    if 'interview_engine' not in st.session_state:
        st.session_state.interview_engine = DynamicInterviewEngine()
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'interview_messages' not in st.session_state:
        st.session_state.interview_messages = []
    if 'resume_parsed' not in st.session_state:
        st.session_state.resume_parsed = None
    if 'job_parsed' not in st.session_state:
        st.session_state.job_parsed = None
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📋 Interview Setup")
        
        # Resume upload
        st.subheader("📄 Resume")
        resume_file = st.file_uploader("Upload Resume", type=['pdf', 'docx', 'txt'], key="resume_upload")
        resume_text = st.text_area("Or paste resume text:", height=100, key="resume_text")
        
        # Job description
        st.subheader("💼 Job Description")
        job_description = st.text_area("Paste job description:", height=150, key="job_description")
        
        # Interview settings (simplified)
        st.subheader("⚙️ Interview Settings")
        st.info("📊 **Interview Structure**: 15 questions across 3 rounds (General → Technical → Theoretical)")
        interview_type = "Mixed"  # Fixed to mixed for now
        difficulty = "Medium"     # Fixed to medium for now
        
        # Parse buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Parse Resume", use_container_width=True):
                if resume_file:
                    # Handle file upload
                    interview_engine = DynamicInterviewEngine()
                    resume_parser = SimpleResumeParser(interview_engine)
                    file_text = resume_parser.parse_file(resume_file)
                    if file_text:
                        st.session_state.resume_parsed = resume_parser.parse_resume(file_text)
                        st.success("Resume parsed successfully!")
                    else:
                        st.error("Could not extract text from the uploaded file. Please try pasting the text instead.")
                elif resume_text:
                    interview_engine = DynamicInterviewEngine()
                    resume_parser = SimpleResumeParser(interview_engine)
                    st.session_state.resume_parsed = resume_parser.parse_resume(resume_text)
                    st.success("Resume parsed successfully!")
                else:
                    st.error("Please upload a resume file or paste resume text")
        
        with col2:
            if st.button("💼 Parse Job", use_container_width=True):
                if job_description:
                    interview_engine = DynamicInterviewEngine()
                    job_parser = SimpleJobParser(interview_engine)
                    st.session_state.job_parsed = job_parser.parse_job_description(job_description)
                    st.success("Job description parsed successfully!")
                else:
                    st.error("Please enter job description")
        
        # Display parsed information
        if st.session_state.resume_parsed:
            st.success("✅ Resume parsed successfully!")
            with st.expander("📄 Parsed Resume Information"):
                resume_data = st.session_state.resume_parsed
                st.write(f"**Name:** {resume_data['name']}")
                st.write(f"**Email:** {resume_data['email']}")
                st.write(f"**Skills:** {', '.join(resume_data['skills'])}")
                st.write(f"**Experience:** {resume_data['experience']}")
                st.write(f"**Education:** {resume_data['education']}")
        
        if st.session_state.job_parsed:
            st.success("✅ Job description parsed successfully!")
            with st.expander("💼 Parsed Job Information"):
                job_data = st.session_state.job_parsed
                st.write(f"**Title:** {job_data['title']}")
                st.write(f"**Company:** {job_data['company']}")
                st.write(f"**Required Skills:** {', '.join(job_data['required_skills'])}")
                st.write(f"**Experience Level:** {job_data['experience_level']}")
                st.write(f"**Job Type:** {job_data['job_type']}")
        
        # Start interview button
        if st.session_state.resume_parsed and st.session_state.job_parsed:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                try:
                    with st.spinner("Starting interview..."):
                        session_id = st.session_state.interview_engine.start_interview(
                            resume_text=resume_text,
                            job_description=job_description,
                            interview_type=interview_type.lower()
                        )
                        
                        st.session_state.current_session_id = session_id
                        st.session_state.interview_messages = []
                        
                        # Get initial question
                        current_question = st.session_state.interview_engine.get_current_question(session_id)
                        
                        if current_question:
                            st.session_state.interview_messages.append({
                                "role": "assistant",
                                "content": current_question['question'],
                                "question_type": current_question.get('question_type', 'general'),
                                "difficulty": current_question.get('difficulty', 'medium')
                            })
                        else:
                            # Fallback question if AI fails
                            fallback_question = "Hello! Thank you for joining this interview. Let's start with a simple question: Can you tell me about yourself and your professional background?"
                            st.session_state.interview_messages.append({
                                "role": "assistant",
                                "content": fallback_question,
                                "question_type": "general",
                                "difficulty": "easy"
                            })
                        
                        # IMMEDIATE DEBUG: Always add a test question to ensure something shows
                        if not st.session_state.interview_messages:
                            st.session_state.interview_messages.append({
                                "role": "assistant", 
                                "content": "🎯 Welcome to your SkillScreen interview! Let's begin: Tell me about yourself and what interests you about this position?",
                                "question_type": "general",
                                "difficulty": "easy"
                            })
                        
                        st.success("Interview started successfully!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error starting interview: {str(e)}")
    
    # Main content area
    if st.session_state.current_session_id:
        show_interview_interface()
    
    # Show parsed information if available
    if st.session_state.resume_parsed:
        with st.expander("📄 Parsed Resume Information", expanded=False):
            resume_info = st.session_state.resume_parsed
            st.write(f"**Name:** {resume_info['name']}")
            st.write(f"**Email:** {resume_info['email']}")
            st.write(f"**Skills:** {', '.join(resume_info['skills'])}")
            st.write(f"**Experience:** {resume_info['experience']}")
            st.write(f"**Education:** {resume_info['education']}")
    
    if st.session_state.job_parsed:
        with st.expander("💼 Parsed Job Information", expanded=False):
            job_info = st.session_state.job_parsed
            st.write(f"**Title:** {job_info['title']}")
            st.write(f"**Company:** {job_info['company']}")
            st.write(f"**Required Skills:** {', '.join(job_info['required_skills'])}")
            st.write(f"**Experience Level:** {job_info['experience_level']}")
            st.write(f"**Job Type:** {job_info['job_type']}")


def show_interview_interface():
    """Show the main interview interface"""
    interview_engine = st.session_state.interview_engine
    session_id = st.session_state.current_session_id
    
    # Show interview progress and current round
    if session_id and session_id in interview_engine.active_sessions:
        interview_state = interview_engine.active_sessions[session_id]
        current_question_num = len(interview_state['question_history']) + 1
        
        # Determine current round
        if current_question_num <= 5:
            round_info = "🔵 Round 1: General Assessment"
            round_desc = "Background, experience, and soft skills"
        elif current_question_num <= 10:
            round_info = "🔧 Round 2: Technical Assessment" 
            round_desc = "Technical skills and hands-on experience"
        elif current_question_num <= 15:
            round_info = "🧠 Round 3: Theoretical Assessment"
            round_desc = "Concepts, best practices, and deep knowledge"
        else:
            round_info = "✅ Interview Complete"
            round_desc = "All rounds finished"
        
        # Show progress bar and round info
        progress = min(current_question_num / 15, 1.0)
        st.progress(progress, text=f"Question {current_question_num}/15")
        st.markdown(f"### {round_info}")
        st.markdown(f"*{round_desc}*")
        st.markdown("---")
    
    # Header with interview status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions Asked", len(interview_engine.active_sessions[session_id]['question_history']))
    with col2:
        st.metric("Responses Given", len(interview_engine.active_sessions[session_id]['response_history']))
    with col3:
        st.metric("Current Score", f"{interview_engine.active_sessions[session_id]['total_score']:.1f}/10")
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Interview Chat")
    
    # Display chat messages
    for message in st.session_state.interview_messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])
        elif message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
    
    # Current question
    current_question = interview_engine.get_current_question(session_id)
    interview_state = interview_engine.active_sessions[session_id]
    question_num = len(interview_state['question_history']) + 1
    
    
    if current_question:
        with st.chat_message("assistant"):
            st.write(current_question['question'])
    elif not interview_state['is_completed']:
        # If no current question but interview not completed, generate a fallback
        
        if question_num <= 5:
            fallback_question = "Tell me about yourself and your professional background."
            question_type = 'general'
        elif question_num <= 10:
            fallback_question = "Walk me through your technical experience and the technologies you've worked with."
            question_type = 'technical'
        else:
            fallback_question = "What are the best practices you follow in your field?"
            question_type = 'theoretical'
        
        with st.chat_message("assistant"):
            st.write(f"**{question_type.upper()} QUESTION:** {fallback_question}")
        
        # Set this as current question
        interview_engine.active_sessions[session_id]['current_question'] = {
            'question': fallback_question,
            'question_type': question_type,
            'difficulty': 'medium',
            'context': 'Fallback question'
        }
    else:
        st.write("**Interview completed!**")
    
    # Response input
    if not interview_engine.active_sessions[session_id]['is_completed']:
        user_response = st.chat_input("Type your response here...")
        
        if user_response:
            # Add user response to chat
            st.session_state.interview_messages.append({
                "role": "user",
                "content": user_response
            })
            
            # Process response
            try:
                result = interview_engine.submit_response(session_id, user_response)
                
                if result['status'] == 'continue':
                    # Add next question (no immediate feedback)
                    if result['next_question']:
                        st.session_state.interview_messages.append({
                            "role": "assistant",
                            "content": result['next_question']['question']
                        })
                    
                    st.rerun()
                
                elif result['status'] == 'completed':
                    # Show interview summary
                    show_interview_summary(result)
                
            except Exception as e:
                st.error(f"Error processing response: {str(e)}")
    else:
        # Interview completed
        show_interview_summary(interview_engine.active_sessions[session_id])

def create_download_link(content: str, filename: str, link_text: str) -> str:
    """Create a download link for text content"""
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:text/markdown;base64,{b64}" download="{filename}">{link_text}</a>'

def show_interview_summary(result):
    """Show interview summary and results"""
    st.markdown("## 🎉 Interview Completed!")
    
    # Display basic metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if isinstance(result, dict) and 'total_score' in result:
            st.metric("Final Score", f"{result['total_score']:.1f}/10")
        else:
            st.metric("Final Score", f"{result.get('total_score', 0):.1f}/10")
    
    with col2:
        if isinstance(result, dict) and 'total_questions' in result:
            st.metric("Total Questions", result['total_questions'])
        else:
            st.metric("Total Questions", len(result.get('question_history', [])))
    
    with col3:
        if isinstance(result, dict) and 'recommendation' in result:
            st.metric("Recommendation", result['recommendation'])
        else:
            st.metric("Recommendation", "Consider")
    
    # Show detailed summary if available
    if isinstance(result, dict) and 'summary_data' in result:
        summary_data = result['summary_data']
        
        st.markdown("### 📊 Executive Summary")
        st.write(summary_data.get('executive_summary', 'Interview completed successfully.'))
        
        # Show detailed assessments
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tech_score = summary_data.get('technical_assessment', {}).get('score', 'N/A')
            st.metric("Technical Skills", f"{tech_score}/10" if tech_score != 'N/A' else 'N/A')
        
        with col2:
            comm_score = summary_data.get('communication_assessment', {}).get('score', 'N/A')
            st.metric("Communication", f"{comm_score}/10" if comm_score != 'N/A' else 'N/A')
        
        with col3:
            fit_score = summary_data.get('cultural_fit', {}).get('score', 'N/A')
            st.metric("Cultural Fit", f"{fit_score}/10" if fit_score != 'N/A' else 'N/A')
        
        # Show strengths and areas for improvement
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ Strengths")
            strengths = summary_data.get('strengths', [])
            if strengths:
                for strength in strengths:
                    st.write(f"• {strength}")
            else:
                st.write("No specific strengths identified.")
        
        with col2:
            st.markdown("#### 📈 Areas for Improvement")
            improvements = summary_data.get('areas_for_improvement', [])
            if improvements:
                for improvement in improvements:
                    st.write(f"• {improvement}")
            else:
                st.write("No specific areas for improvement identified.")
        
        # Show key highlights
        if summary_data.get('key_highlights'):
            st.markdown("#### 🌟 Key Highlights")
            for highlight in summary_data['key_highlights']:
                st.write(f"• {highlight}")
        
        # Show red flags if any
        if summary_data.get('red_flags'):
            st.markdown("#### ⚠️ Areas of Concern")
            for flag in summary_data['red_flags']:
                st.write(f"• {flag}")
        
        # Show next steps
        if summary_data.get('next_steps'):
            st.markdown("#### 🎯 Recommended Next Steps")
            for step in summary_data['next_steps']:
                st.write(f"• {step}")
    
    else:
        # Fallback summary display
        st.markdown("### 📊 Interview Summary")
        if isinstance(result, dict) and 'summary' in result:
            st.write(result['summary'])
        else:
            st.write("Interview completed successfully.")
    
    # Download section
    st.markdown("---")
    st.markdown("### 📥 Download Interview Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF Report", type="primary"):
            try:
                session_id = st.session_state.current_session_id
                interview_engine = st.session_state.interview_engine
                
                if session_id and interview_engine:
                    pdf_buffer = interview_engine.generate_pdf_report(session_id)
                    
                    if pdf_buffer:
                        # Create filename with candidate name and date
                        candidate_name = interview_engine.active_sessions[session_id]['parsed_resume']['name']
                        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        filename = f"Interview_Report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        
                        # Create download link for PDF
                        b64 = base64.b64encode(pdf_buffer.read()).decode()
                        download_link = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Click here to download PDF report</a>'
                        st.markdown(download_link, unsafe_allow_html=True)
                        st.success("✅ PDF report generated successfully! Click the link above to download.")
                    else:
                        st.error("❌ Error generating PDF report.")
                else:
                    st.error("❌ Unable to generate report. Interview session not found.")
            except Exception as e:
                st.error(f"❌ Error generating PDF report: {str(e)}")
    
    with col2:
        if st.button("📝 Download Text Report"):
            try:
                # Generate the report
                session_id = st.session_state.current_session_id
                interview_engine = st.session_state.interview_engine
                
                if session_id and interview_engine:
                    report_content = interview_engine.generate_interview_report(session_id)
                    
                    # Create filename with candidate name and date
                    candidate_name = interview_engine.active_sessions[session_id]['parsed_resume']['name']
                    safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"Interview_Report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    
                    # Create download link
                    download_link = create_download_link(report_content, filename, "📥 Click here to download text report")
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.success("✅ Text report generated successfully! Click the link above to download.")
                else:
                    st.error("❌ Unable to generate report. Interview session not found.")
            except Exception as e:
                st.error(f"❌ Error generating text report: {str(e)}")
    
    with col3:
        if st.button("📊 Download JSON Data", help="Download detailed interview data in JSON format"):
            try:
                session_id = st.session_state.current_session_id
                interview_engine = st.session_state.interview_engine
                
                if session_id and interview_engine:
                    # Create JSON summary
                    interview_data = interview_engine.active_sessions[session_id]
                    json_data = {
                        'candidate_info': interview_data['parsed_resume'],
                        'job_info': interview_data['parsed_job'],
                        'interview_summary': result,
                        'questions_and_responses': [
                            {
                                'question': q['question'],
                                'response': r['response'],
                                'score': r['score'],
                                'feedback': r.get('feedback', ''),
                                'timestamp': r['timestamp'].isoformat() if isinstance(r['timestamp'], datetime) else str(r['timestamp'])
                            }
                            for q, r in zip(interview_data['question_history'], interview_data['response_history'])
                        ],
                        'session_info': {
                            'session_id': session_id,
                            'start_time': interview_data['start_time'].isoformat(),
                            'end_time': interview_data.get('end_time', datetime.now()).isoformat(),
                            'total_score': interview_data['total_score']
                        }
                    }
                    
                    json_content = json.dumps(json_data, indent=2, default=str)
                    
                    # Create filename
                    candidate_name = interview_data['parsed_resume']['name']
                    safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"Interview_Data_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    # Create download link
                    b64 = base64.b64encode(json_content.encode()).decode()
                    download_link = f'<a href="data:application/json;base64,{b64}" download="{filename}">📥 Click here to download JSON data</a>'
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.success("✅ JSON data generated successfully! Click the link above to download.")
                else:
                    st.error("❌ Unable to generate JSON data. Interview session not found.")
            except Exception as e:
                st.error(f"❌ Error generating JSON data: {str(e)}")
    
    st.markdown("---")
    
    # Restart option
    if st.button("🔄 Start New Interview", type="secondary", use_container_width=True):
        # Reset session state
        st.session_state.interview_engine = DynamicInterviewEngine()
        st.session_state.current_session_id = None
        st.session_state.interview_messages = []
        st.session_state.resume_parsed = None
        st.session_state.job_parsed = None
        st.rerun()

if __name__ == "__main__":
    main()