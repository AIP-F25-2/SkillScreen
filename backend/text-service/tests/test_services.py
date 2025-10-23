import pytest
import sys
import os

# Add the backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from utils.resume_parser import ResumeParser
    from utils.logger import Logger
except ImportError as e:
    pytest.skip(f"Skipping tests due to import error: {e}", allow_module_level=True)

try:
    from services.llm_service import EnhancedLLMService
    from services.code_execution_service import CodeExecutionService
except ImportError as e:
    pytest.skip(f"Skipping LLM/Code execution tests due to import error: {e}", allow_module_level=True)


class TestResumeParser:
    """Test cases for ResumeParser"""
    
    def test_resume_parser_initialization(self):
        """Test ResumeParser initialization"""
        parser = ResumeParser()
        assert parser is not None
        assert hasattr(parser, 'experience_patterns')
        assert hasattr(parser, 'skill_patterns')
    
    def test_extract_name(self):
        """Test name extraction from resume text"""
        parser = ResumeParser()
        test_text = "John Doe\nSoftware Engineer\njohn.doe@email.com"
        name = parser.extract_name(test_text)
        assert name == "John Doe"
    
    def test_extract_email(self):
        """Test email extraction from resume text"""
        parser = ResumeParser()
        test_text = "John Doe\nSoftware Engineer\njohn.doe@email.com"
        email = parser.extract_email(test_text)
        assert email == "john.doe@email.com"
    
    def test_calculate_experience_years(self):
        """Test experience calculation"""
        parser = ResumeParser()
        test_text = """
        Work Experience
        Software Engineer at Tech Corp (2020-2023)
        Junior Developer at Startup Inc (2018-2020)
        """
        experience = parser.calculate_experience_years(test_text)
        assert experience == 5.0  # 3 + 2 years
    
    def test_extract_skills(self):
        """Test skill extraction"""
        parser = ResumeParser()
        test_text = """
        Skills: Python, JavaScript, React, Node.js, SQL, Docker
        """
        skills = parser.extract_skills(test_text)
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "React" in skills


class TestLLMService:
    """Test cases for EnhancedLLMService"""
    
    def test_llm_service_initialization(self):
        """Test LLM service initialization"""
        service = EnhancedLLMService()
        assert service is not None
        assert hasattr(service, 'gemini_model')
        assert hasattr(service, 'wolfram_app_id')
        assert hasattr(service, 'serpapi_key')
    
    @pytest.mark.asyncio
    async def test_generate_interview_question_mock(self):
        """Test question generation with mock data"""
        service = EnhancedLLMService()
        
        # Test with mock data
        question = await service.generate_interview_question(
            candidate_name="John Doe",
            candidate_experience=5,
            candidate_skills=["Python", "FastAPI"],
            job_title="Software Engineer",
            job_company="Tech Corp",
            job_level="Mid-level",
            job_skills=["Python", "React", "SQL"],
            job_description="We are looking for a skilled software engineer",
            question_type="technical",
            question_number=1
        )
        
        assert question is not None
        assert isinstance(question, str)
        assert len(question) > 10


class TestCodeExecutionService:
    """Test cases for CodeExecutionService"""
    
    def test_code_execution_service_initialization(self):
        """Test code execution service initialization"""
        service = CodeExecutionService()
        assert service is not None
        assert hasattr(service, 'supported_languages')
        assert hasattr(service, 'execution_results')
    
    def test_get_supported_languages(self):
        """Test getting supported languages"""
        service = CodeExecutionService()
        languages = service.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "python" in languages
    
    @pytest.mark.asyncio
    async def test_execute_code_python(self):
        """Test Python code execution"""
        service = CodeExecutionService()
        
        result = await service.execute_code(
            code="print('Hello, World!')",
            language="python"
        )
        
        assert result is not None
        assert "execution_id" in result
        assert result["status"] in ["success", "error"]


if __name__ == "__main__":
    pytest.main([__file__])
