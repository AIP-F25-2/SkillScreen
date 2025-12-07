import json
from typing import Dict, Optional, List
import google.generativeai as genai
from groq import Groq
from config import logger, settings
from repositories import InterviewRepository, QuestionRepository
import uuid
from datetime import datetime, timezone


class QuestionGenerationService:
    """Service for AI-powered question generation using Google Gemini"""

    def __init__(self):
        self.interview_repo = InterviewRepository()
        self.question_repo = QuestionRepository()

        # Initialize Gemini API
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set")
            self.model = None

        # Initialize Groq API as fallback
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        else:
            logger.warning("⚠️ GROQ_API_KEY not set - Groq fallback unavailable")
            self.groq_client = None

    def generate_interview_questions(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str,
        num_questions: int = None,
        difficulty_level: str = None
    ) -> Dict:
        """Generate first question (tell me about yourself) for interview"""
        try:
            # Get interview to check settings
            interview = self.interview_repo.get_interview_by_id(interview_id)
            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            # Use settings from interview or defaults
            interview_settings = interview.get("settings", {})
            if num_questions is None:
                # Check both max_questions and num_questions keys
                num_questions = interview_settings.get("max_questions") or interview_settings.get("num_questions") or settings.QUESTIONS_PER_INTERVIEW

            if difficulty_level is None:
                difficulty_level = interview_settings.get("difficulty", "medium")

            # Get candidate and job info
            candidate = self.interview_repo.get_candidate_by_id(candidate_id)
            job = self.interview_repo.get_job_position_by_id(job_position_id)

            if not candidate:
                return {
                    "success": False,
                    "error": f"Candidate not found: {candidate_id}"
                }

            if not job:
                return {
                    "success": False,
                    "error": f"Job position not found: {job_position_id}"
                }

            logger.info(f"🔄 Generating first question for interview {interview_id}")

            # Always start with "Tell me about yourself" - introductory question
            first_session_data = {
                "id": str(uuid.uuid4()),
                "interview_id": interview_id,
                "question_id": str(uuid.uuid4()),
                "question_text": "Tell me about yourself, including your background, experience, and why you're interested in this role.",
                "question_type": "behavioral",
                "candidate_response": None,
                "response_duration": None,
                "started_at": None,
                "completed_at": None,
                "metadata": {
                    "difficulty": difficulty_level,
                    "expected_points": ["Background", "Experience", "Motivation for the role", "Relevant skills"],
                    "generated_by": "system",
                    "question_index": 1,
                    "total_questions": num_questions
                }
            }

            # Save first session to database
            session_id = self.question_repo.create_session(first_session_data)

            # Update the session_id in the returned data to match DB
            first_session_data["id"] = session_id
            saved_sessions = [first_session_data]

            # Verify session was saved
            verify_session = self.question_repo.get_session_by_id(session_id)
            if verify_session:
                logger.info(f"✅ Generated and verified first question - Session ID: {session_id}")
            else:
                logger.warning(f"⚠️ First question created but verification failed - Session ID: {session_id}")
                # Return the data anyway as it should be persisted
                logger.info(f"✅ Generated first question (Tell me about yourself)")

            return {
                "success": True,
                "data": {
                    "interview_id": interview_id,
                    "questions_generated": 1,  # Only first question generated upfront
                    "sessions": saved_sessions,
                    "note": "Remaining questions will be generated dynamically based on candidate responses"
                }
            }

        except Exception as e:
            logger.error(f"❌ Error generating first question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_question_generation_prompt(self, candidate: Dict, job: Dict, num_questions: int) -> str:
        """Build prompt for Gemini to generate interview questions"""
        candidate_skills = candidate.get("skills", [])
        candidate_experience = candidate.get("experience", [])
        job_skills = job.get("required_skills", [])

        prompt = f"""
        Generate {num_questions} interview questions for the following scenario:

        CANDIDATE:
        - Name: {candidate.get('full_name')}
        - Skills: {json.dumps(candidate_skills)}
        - Experience: {json.dumps(candidate_experience)}

        JOB POSITION:
        - Title: {job.get('title')}
        - Description: {job.get('description')}
        - Required Skills: {json.dumps(job_skills)}
        - Department: {job.get('department')}

        REQUIREMENTS:
        - Mix question types: technical (40%), behavioral (40%), situational (20%)
        - Vary difficulty levels appropriately
        - Focus on gaps between candidate skills and job requirements
        - Each question should be answerable in 1-2 minutes
        - Include follow-up opportunities

        RESPONSE FORMAT:
        Return a JSON object with this structure:
        {{
            "questions": [
                {{
                    "text": "Question text here",
                    "type": "technical|behavioral|situational",
                    "difficulty": "easy|medium|hard",
                    "expected_points": ["point1", "point2", "point3"]
                }}
            ]
        }}

        Return ONLY the JSON object, no other text.
        """

        return prompt.strip()

    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini response and extract questions"""
        try:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"questions": []}
        except json.JSONDecodeError:
            logger.warning("⚠️ Failed to parse Gemini response")
            return {"questions": []}

    def _generate_with_groq(self, prompt: str) -> Dict:
        """Generate questions using Groq API as fallback"""
        try:
            message = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                max_tokens=settings.MAX_TOKENS_RESPONSE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = message.choices[0].message.content
            return self._parse_gemini_response(response_text)
        except Exception as e:
            logger.error(f"❌ Groq generation failed: {str(e)}")
            raise

    def _get_default_questions(self, num_questions: int) -> Dict:
        """Get default questions when Gemini is unavailable"""
        default_questions = [
            {
                "text": "Tell me about a challenging project you worked on and how you overcame the challenges.",
                "type": "behavioral",
                "difficulty": "medium",
                "expected_points": ["Problem identification", "Solution approach", "Outcome", "Learning"]
            },
            {
                "text": "Describe your approach to learning new technologies or frameworks.",
                "type": "behavioral",
                "difficulty": "medium",
                "expected_points": ["Learning methods", "Examples", "Continuous improvement", "Adaptability"]
            },
            {
                "text": "How do you handle disagreements with team members or managers?",
                "type": "behavioral",
                "difficulty": "medium",
                "expected_points": ["Communication", "Collaboration", "Professionalism", "Problem resolution"]
            },
            {
                "text": "What are your strongest technical skills and why?",
                "type": "technical",
                "difficulty": "easy",
                "expected_points": ["Skills clarity", "Depth of knowledge", "Practical examples"]
            },
            {
                "text": "Describe a situation where you had to meet a tight deadline. How did you manage it?",
                "type": "situational",
                "difficulty": "medium",
                "expected_points": ["Time management", "Prioritization", "Results", "Stress handling"]
            }
        ]

        return {"questions": default_questions[:num_questions]}

    def regenerate_session_question(
        self,
        session_id: str,
        feedback: Optional[str] = None
    ) -> Dict:
        """Regenerate a specific session question based on feedback"""
        try:
            session = self.question_repo.get_session_by_id(session_id)

            if not session:
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}"
                }

            interview = self.interview_repo.get_interview_by_id(session["interview_id"])

            if not interview:
                return {
                    "success": False,
                    "error": "Associated interview not found"
                }

            # Get new question
            new_question = self._generate_single_question(
                interview,
                session["question_type"],
                feedback
            )

            if not new_question:
                return {
                    "success": False,
                    "error": "Failed to generate new question"
                }

            # Update the session with new question
            updated_data = {
                "question_text": new_question.get("text"),
                "metadata": {
                    "expected_points": new_question.get("expected_points", []),
                    "generated_by": "gemini",
                    "regenerated": True
                }
            }

            # We need a method to update session questions, would update via direct update
            # For now return the new question data

            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "new_question": new_question
                }
            }

        except Exception as e:
            logger.error(f"❌ Error regenerating question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_next_question(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str,
        previous_response: str = None,
        question_count: int = None
    ) -> Dict:
        """Generate next question dynamically based on previous response, resume, and job description"""
        try:
            # Get interview, candidate, and job info
            interview = self.interview_repo.get_interview_by_id(interview_id)
            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            candidate = self.interview_repo.get_candidate_by_id(candidate_id)
            job = self.interview_repo.get_job_position_by_id(job_position_id)

            if not candidate:
                return {
                    "success": False,
                    "error": f"Candidate not found: {candidate_id}"
                }

            if not job:
                return {
                    "success": False,
                    "error": f"Job position not found: {job_position_id}"
                }

            # Get all existing sessions to determine next question index
            existing_sessions = self.question_repo.get_sessions_by_interview(interview_id)
            next_index = len(existing_sessions) + 1

            # Get total questions from settings (check both max_questions and num_questions keys)
            interview_settings = interview.get("settings", {})
            total_questions = interview_settings.get("max_questions") or interview_settings.get("num_questions") or settings.QUESTIONS_PER_INTERVIEW
            difficulty = interview_settings.get("difficulty", "medium")

            # CHECK: If we've already reached max questions, don't generate more
            if next_index > total_questions:
                logger.info(f"⛔ Interview completed - already asked {len(existing_sessions)} of {total_questions} questions")
                return {
                    "success": False,
                    "error": f"Interview already completed - maximum {total_questions} questions reached",
                    "completed": True,
                    "questions_asked": len(existing_sessions),
                    "max_questions": total_questions
                }

            # Build prompt for dynamic question generation
            prompt = self._build_dynamic_question_prompt(
                candidate=candidate,
                job=job,
                previous_response=previous_response,
                question_index=next_index,
                total_questions=total_questions,
                difficulty=difficulty
            )

            logger.info(f"🔄 Generating question {next_index} for interview {interview_id}")

            # Call Gemini API first, fallback to Groq, then default questions
            question_json = None
            if self.model:
                try:
                    response = self.model.generate_content(prompt)
                    question_json = self._parse_gemini_response(response.text)
                except Exception as gemini_error:
                    error_msg = str(gemini_error)
                    if "quota" in error_msg.lower() or "429" in error_msg or "resource exhausted" in error_msg.lower():
                        logger.warning(f"⚠️ Gemini API quota exceeded, trying Groq fallback")
                        if self.groq_client:
                            try:
                                question_json = self._generate_with_groq(prompt)
                            except Exception as groq_error:
                                logger.warning(f"⚠️ Groq generation failed: {str(groq_error)}, using default question")
                                question_json = self._get_default_next_question(next_index, total_questions, difficulty)
                        else:
                            logger.warning("⚠️ Groq not available, using default question")
                            question_json = self._get_default_next_question(next_index, total_questions, difficulty)
                    else:
                        raise
            else:
                logger.warning("⚠️ Gemini model not initialized, trying Groq")
                if self.groq_client:
                    try:
                        question_json = self._generate_with_groq(prompt)
                    except Exception as groq_error:
                        logger.warning(f"⚠️ Groq generation failed: {str(groq_error)}, using default question")
                        question_json = self._get_default_next_question(next_index, total_questions, difficulty)
                else:
                    question_json = self._get_default_next_question(next_index, total_questions, difficulty)

            if not question_json.get("questions") or len(question_json["questions"]) == 0:
                return {
                    "success": False,
                    "error": "Failed to generate next question"
                }

            question_data = question_json["questions"][0]

            # Create session for new question
            next_session_data = {
                "id": str(uuid.uuid4()),
                "interview_id": interview_id,
                "question_id": str(uuid.uuid4()),
                "question_text": question_data.get("text"),
                "question_type": question_data.get("type", "behavioral"),
                "candidate_response": None,
                "response_duration": None,
                "started_at": None,
                "completed_at": None,
                "metadata": {
                    "difficulty": difficulty,
                    "expected_points": question_data.get("expected_points", []),
                    "generated_by": "gemini",
                    "question_index": next_index,
                    "total_questions": total_questions,
                    "based_on_response": bool(previous_response)
                }
            }

            self.question_repo.create_session(next_session_data)

            logger.info(f"✅ Generated question {next_index}/{total_questions}")

            return {
                "success": True,
                "data": next_session_data
            }

        except Exception as e:
            logger.error(f"❌ Error generating next question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_dynamic_question_prompt(
        self,
        candidate: Dict,
        job: Dict,
        previous_response: Optional[str],
        question_index: int,
        total_questions: int,
        difficulty: str
    ) -> str:
        """Build prompt for Gemini to generate next question based on context"""
        candidate_skills = candidate.get("skills", [])
        candidate_experience = candidate.get("experience", [])
        job_skills = job.get("required_skills", [])

        prompt = f"""
        Generate the next interview question (question {question_index} of {total_questions}) for the following scenario:

        CANDIDATE:
        - Name: {candidate.get('full_name')}
        - Skills: {json.dumps(candidate_skills)}
        - Experience: {json.dumps(candidate_experience)}

        JOB POSITION:
        - Title: {job.get('title')}
        - Description: {job.get('description')}
        - Required Skills: {json.dumps(job_skills)}
        - Department: {job.get('department')}

        DIFFICULTY LEVEL: {difficulty}
        """

        if previous_response:
            prompt += f"""

        CANDIDATE'S PREVIOUS RESPONSE:
        {previous_response}

        INSTRUCTIONS:
        - Analyze the candidate's previous response for gaps, strengths, and areas to explore
        - Generate a follow-up question that:
          * Digs deeper into their experience or qualifications
          * Addresses skill gaps between their profile and job requirements
          * Tests specific technical or soft skills needed for the role
          * Is appropriate for the difficulty level ({difficulty})
        """
        else:
            prompt += """

        INSTRUCTIONS:
        - Generate a question appropriate for the difficulty level and interview stage
        - Vary question types: mix technical, behavioral, and situational questions
        - Focus on job requirements and skill alignment
        """

        prompt += """

        RESPONSE FORMAT:
        Return a JSON object with this structure:
        {
            "questions": [
                {
                    "text": "Question text here",
                    "type": "technical|behavioral|situational",
                    "expected_points": ["point1", "point2", "point3"]
                }
            ]
        }

        Return ONLY the JSON object, no other text.
        """

        return prompt.strip()

    def _get_default_next_question(self, question_index: int, total_questions: int, difficulty: str) -> Dict:
        """Get default next question when Gemini is unavailable"""
        default_progressions = [
            {
                "text": "Can you describe a specific project where you had to apply the skills you mentioned?",
                "type": "behavioral",
                "expected_points": ["Specific project", "Skills applied", "Outcome", "Challenges faced"]
            },
            {
                "text": "How do you stay current with industry trends and new technologies?",
                "type": "behavioral",
                "expected_points": ["Learning methods", "Resources used", "Recent learning", "Application to work"]
            },
            {
                "text": "Tell us about a time when you had to work with a difficult team member. How did you handle it?",
                "type": "behavioral",
                "expected_points": ["Situation description", "Communication approach", "Resolution", "Outcome"]
            },
            {
                "text": "What would you consider your greatest professional achievement?",
                "type": "behavioral",
                "expected_points": ["Achievement", "Impact", "Role played", "Skills demonstrated"]
            },
            {
                "text": "How do you approach problem-solving when faced with an unfamiliar challenge?",
                "type": "technical",
                "expected_points": ["Approach", "Tools/Methods", "Research strategy", "Example"]
            }
        ]

        selected_idx = min(question_index - 2, len(default_progressions) - 1)
        selected = default_progressions[selected_idx]

        return {"questions": [selected]}

    def _generate_single_question(self, interview: Dict, question_type: str, feedback: Optional[str] = None) -> Dict:
        """Generate a single question"""
        try:
            if not self.model:
                return None

            prompt = f"""
            Generate a single {question_type} interview question.
            """

            if feedback:
                prompt += f"\nFeedback on previous question: {feedback}"

            prompt += "\nReturn as JSON: {{'text': '...', 'type': '...', 'difficulty': '...', 'expected_points': [...]}}"

            response = self.model.generate_content(prompt)
            return self._parse_gemini_response(response.text).get("questions", [{}])[0]

        except Exception as e:
            logger.error(f"Error generating single question: {str(e)}")
            return None
