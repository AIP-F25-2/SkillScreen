"""
Interview service for orchestrating the complete interview process
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import asyncio
import logging

from database.models import (
    Interview, InterviewQuestion, InterviewResponse, 
    InterviewSummary, Candidate, Job, AuditLog
)
from services.nlp_service import NLPService
from services.anti_cheating_service import AntiCheatingService
from services.rag_service import RAGExplainabilityService
from utils.logger import log_info, log_error, log_warning

class InterviewService:
    """Orchestrates the complete interview process"""
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.anti_cheating_service = AntiCheatingService()
        self.rag_service = RAGExplainabilityService()
        
        # Interview configuration
        self.question_templates = {
            'general': [
                "Tell me about yourself and your professional background.",
                "What are your key strengths and how do they apply to this role?",
                "Describe a challenging situation you faced and how you handled it.",
                "What motivates you in your work and career?",
                "Tell me about a time when you had to work collaboratively in a team."
            ],
            'technical': [
                "Walk me through your technical experience and the technologies you've worked with.",
                "Describe a complex technical project you've worked on recently.",
                "How do you approach debugging and troubleshooting technical issues?",
                "What development tools and methodologies do you prefer and why?",
                "Tell me about a time when you had to learn a new technology quickly."
            ],
            'theoretical': [
                "What are the best practices you follow in your field?",
                "How do you ensure code quality and maintainability in your projects?",
                "Explain your approach to system design and architecture decisions.",
                "What industry trends do you think will shape the future of this field?",
                "How do you balance performance, scalability, and maintainability in your work?"
            ]
        }
    
    async def generate_initial_question(
        self,
        candidate: Candidate,
        job: Job,
        interview_type: str,
        db
    ) -> Dict:
        """Generate the initial interview question"""
        try:
            # Create context for question generation
            context = {
                'candidate_name': candidate.name,
                'candidate_skills': candidate.skills or [],
                'candidate_experience': candidate.experience_years or 0,
                'job_title': job.title,
                'job_company': job.company,
                'job_skills': job.skills_required or [],
                'job_level': job.experience_level or 'Mid-level'
            }
            
            # Generate personalized question
            question_text = await self._generate_personalized_question(
                'general', context, interview_type
            )
            
            # Create question record
            question = InterviewQuestion(
                question_index=0,
                question_text=question_text,
                question_type='general',
                difficulty='medium',
                round_number=1,
                context=json.dumps(context)
            )
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': 0,
                'question_text': question_text,
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': context,
                'asked_at': datetime.utcnow()
            }
            
        except Exception as e:
            log_error(f"Error generating initial question: {e}")
            return {
                'id': str(uuid.uuid4()),
                'question_index': 0,
                'question_text': "Tell me about yourself and your professional background.",
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': {},
                'asked_at': datetime.utcnow()
            }
    
    async def generate_next_question(
        self,
        interview_id: str,
        db
    ) -> Dict:
        """Generate the next question based on interview progress"""
        try:
            # Get interview and previous questions
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            previous_questions = db.query(InterviewQuestion).filter(
                InterviewQuestion.interview_id == interview_id
            ).order_by(InterviewQuestion.question_index).all()
            
            # Determine question type based on progress
            current_question_index = len(previous_questions)
            question_type, round_number = self._determine_question_type(current_question_index)
            
            # Get candidate and job context
            candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
            job = db.query(Job).filter(Job.id == interview.job_id).first()
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Create context for question generation
            context = {
                'candidate_name': candidate.name,
                'candidate_skills': candidate.skills or [],
                'candidate_experience': candidate.experience_years or 0,
                'job_title': job.title,
                'job_company': job.company,
                'job_skills': job.skills_required or [],
                'job_level': job.experience_level or 'Mid-level',
                'previous_questions': [q.question_text for q in previous_questions],
                'current_round': round_number
            }
            
            # Generate personalized question
            question_text = await self._generate_personalized_question(
                question_type, context, interview.interview_type
            )
            
            # Create question record
            question = InterviewQuestion(
                interview_id=interview_id,
                question_index=current_question_index,
                question_text=question_text,
                question_type=question_type,
                difficulty='medium',
                round_number=round_number,
                context=json.dumps(context)
            )
            
            db.add(question)
            db.commit()
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': question_text,
                'question_type': question_type,
                'difficulty': 'medium',
                'round_number': round_number,
                'context': context,
                'asked_at': datetime.utcnow()
            }
            
        except Exception as e:
            log_error(f"Error generating next question: {e}")
            # Return fallback question
            return {
                'id': str(uuid.uuid4()),
                'question_index': len(previous_questions) if 'previous_questions' in locals() else 0,
                'question_text': "Can you tell me more about your experience in this field?",
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': {},
                'asked_at': datetime.utcnow()
            }
    
    async def generate_interview_summary(
        self,
        interview_id: str,
        db
    ) -> Dict:
        """Generate comprehensive interview summary"""
        try:
            # Get interview data
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
            job = db.query(Job).filter(Job.id == interview.job_id).first()
            responses = db.query(InterviewResponse).filter(
                InterviewResponse.interview_id == interview_id
            ).order_by(InterviewResponse.received_at).all()
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Calculate overall metrics
            total_responses = len(responses)
            if total_responses > 0:
                overall_score = sum(r.overall_score for r in responses if r.overall_score is not None) / total_responses
                avg_response_length = sum(len(r.response_text) for r in responses) / total_responses
            else:
                overall_score = 0.0
                avg_response_length = 0.0
            
            # Analyze response patterns
            duplicate_responses = sum(1 for r in responses if r.is_duplicate)
            off_topic_responses = sum(1 for r in responses if r.is_off_topic)
            
            # Generate detailed assessments
            technical_assessment = await self._generate_technical_assessment(responses, job)
            communication_assessment = await self._generate_communication_assessment(responses)
            cultural_fit_assessment = await self._generate_cultural_fit_assessment(responses, candidate, job)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                candidate, job, overall_score, total_responses, duplicate_responses, off_topic_responses
            )
            
            # Determine recommendation
            recommendation, recommendation_reason = await self._determine_recommendation(
                overall_score, duplicate_responses, off_topic_responses, total_responses
            )
            
            # Generate strengths and weaknesses
            strengths, weaknesses = await self._generate_strengths_weaknesses(responses)
            
            # Generate improvement tips
            improvement_tips = await self._generate_improvement_tips(responses, job)
            
            # Create summary data
            summary_data = {
                'executive_summary': executive_summary,
                'overall_score': round(overall_score, 1),
                'recommendation': recommendation,
                'recommendation_reason': recommendation_reason,
                'technical_assessment': technical_assessment,
                'communication_assessment': communication_assessment,
                'cultural_fit': cultural_fit_assessment,
                'strengths': strengths,
                'areas_for_improvement': weaknesses,
                'key_highlights': await self._generate_key_highlights(responses),
                'red_flags': await self._generate_red_flags(responses, duplicate_responses, off_topic_responses),
                'improvement_tips': improvement_tips,
                'next_steps': await self._generate_next_steps(recommendation, overall_score),
                'interviewer_notes': await self._generate_interviewer_notes(
                    candidate, job, overall_score, total_responses, duplicate_responses, off_topic_responses
                )
            }
            
            # Save summary to database
            summary = InterviewSummary(
                interview_id=interview_id,
                executive_summary=executive_summary,
                overall_score=overall_score,
                recommendation=recommendation,
                recommendation_reason=recommendation_reason,
                technical_assessment_score=technical_assessment['score'],
                technical_assessment_summary=technical_assessment['summary'],
                communication_assessment_score=communication_assessment['score'],
                communication_assessment_summary=communication_assessment['summary'],
                cultural_fit_score=cultural_fit_assessment['score'],
                cultural_fit_summary=cultural_fit_assessment['summary'],
                strengths=strengths,
                areas_for_improvement=weaknesses,
                key_highlights=summary_data['key_highlights'],
                red_flags=summary_data['red_flags'],
                improvement_tips=improvement_tips,
                next_steps=summary_data['next_steps'],
                interviewer_notes=summary_data['interviewer_notes']
            )
            
            db.add(summary)
            
            # Update interview with final score
            interview.overall_score = overall_score
            interview.end_time = datetime.utcnow()
            interview.status = 'completed'
            
            db.commit()
            
            log_info(f"Generated interview summary for {interview_id}")
            
            return summary_data
            
        except Exception as e:
            log_error(f"Error generating interview summary: {e}")
            return self._fallback_summary()
    
    async def generate_pdf_report(
        self,
        interview_id: str,
        db
    ) -> str:
        """Generate PDF report for interview"""
        try:
            # This would integrate with the existing PDF generation logic
            # For now, return a placeholder
            return f"reports/interview_{interview_id}_report.pdf"
            
        except Exception as e:
            log_error(f"Error generating PDF report: {e}")
            raise
    
    def _determine_question_type(self, question_index: int) -> tuple:
        """Determine question type and round based on index"""
        if question_index < 5:
            return 'general', 1
        elif question_index < 10:
            return 'technical', 2
        else:
            return 'theoretical', 3
    
    async def _generate_personalized_question(
        self,
        question_type: str,
        context: Dict,
        interview_type: str
    ) -> str:
        """Generate personalized question based on context"""
        try:
            # Use NLP service to generate personalized question
            if hasattr(self.nlp_service, 'models') and self.nlp_service.models:
                prompt = f"""
                Generate a personalized {question_type} interview question for:
                
                Candidate: {context['candidate_name']}
                Skills: {', '.join(context['candidate_skills'][:5])}
                Experience: {context['candidate_experience']} years
                
                Job: {context['job_title']} at {context['job_company']}
                Required Skills: {', '.join(context['job_skills'][:5])}
                Level: {context['job_level']}
                
                Previous questions: {', '.join(context.get('previous_questions', [])[-3:])}
                
                Generate a unique, engaging question that hasn't been asked before.
                """
                
                # This would use the NLP service to generate the question
                # For now, use template-based approach
                pass
            
            # Fallback to template-based question generation
            templates = self.question_templates.get(question_type, self.question_templates['general'])
            question_index = context.get('current_round', 1) - 1
            
            if question_index < len(templates):
                base_question = templates[question_index]
            else:
                base_question = templates[0]
            
            # Personalize the question
            personalized_question = base_question
            
            # Add job-specific elements
            if context['job_skills']:
                skills_mention = f" particularly with {', '.join(context['job_skills'][:2])}"
                personalized_question = personalized_question.replace(
                    "in this field", f"in {context['job_title']}{skills_mention}"
                )
            
            return personalized_question
            
        except Exception as e:
            log_warning(f"Error generating personalized question: {e}")
            return self.question_templates[question_type][0]
    
    async def _generate_technical_assessment(
        self,
        responses: List[InterviewResponse],
        job: Job
    ) -> Dict:
        """Generate technical assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No technical responses to evaluate'
                }
            
            # Calculate technical score
            technical_scores = [r.technical_accuracy_score for r in responses if r.technical_accuracy_score is not None]
            if technical_scores:
                avg_technical_score = sum(technical_scores) / len(technical_scores)
            else:
                avg_technical_score = 0.0
            
            # Generate summary
            if avg_technical_score >= 8:
                summary = "Demonstrated strong technical knowledge with specific examples and relevant experience"
            elif avg_technical_score >= 6:
                summary = "Showed good technical understanding with some specific examples"
            elif avg_technical_score >= 4:
                summary = "Basic technical knowledge demonstrated but lacks depth and specificity"
            else:
                summary = "Limited technical knowledge shown, significant gaps in required skills"
            
            return {
                'score': round(avg_technical_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating technical assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Technical assessment completed'
            }
    
    async def _generate_communication_assessment(
        self,
        responses: List[InterviewResponse]
    ) -> Dict:
        """Generate communication assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No communication responses to evaluate'
                }
            
            # Calculate communication score
            comm_scores = [r.communication_score for r in responses if r.communication_score is not None]
            if comm_scores:
                avg_comm_score = sum(comm_scores) / len(comm_scores)
            else:
                avg_comm_score = 0.0
            
            # Generate summary
            if avg_comm_score >= 8:
                summary = "Excellent communication skills with clear, structured, and professional responses"
            elif avg_comm_score >= 6:
                summary = "Good communication skills with generally clear and professional responses"
            elif avg_comm_score >= 4:
                summary = "Adequate communication skills but responses could be more structured and clear"
            else:
                summary = "Communication skills need improvement in clarity, structure, and professionalism"
            
            return {
                'score': round(avg_comm_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating communication assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Communication assessment completed'
            }
    
    async def _generate_cultural_fit_assessment(
        self,
        responses: List[InterviewResponse],
        candidate: Candidate,
        job: Job
    ) -> Dict:
        """Generate cultural fit assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No responses to evaluate cultural fit'
                }
            
            # Calculate job fit score
            fit_scores = [r.job_fit_score for r in responses if r.job_fit_score is not None]
            if fit_scores:
                avg_fit_score = sum(fit_scores) / len(fit_scores)
            else:
                avg_fit_score = 0.0
            
            # Generate summary
            if avg_fit_score >= 8:
                summary = "Strong alignment with role requirements and company culture"
            elif avg_fit_score >= 6:
                summary = "Good fit with role requirements and cultural indicators"
            elif avg_fit_score >= 4:
                summary = "Moderate fit with some alignment to role requirements"
            else:
                summary = "Limited fit with role requirements and cultural expectations"
            
            return {
                'score': round(avg_fit_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating cultural fit assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Cultural fit assessment completed'
            }
    
    async def _generate_executive_summary(
        self,
        candidate: Candidate,
        job: Job,
        overall_score: float,
        total_responses: int,
        duplicate_responses: int,
        off_topic_responses: int
    ) -> str:
        """Generate executive summary"""
        try:
            summary_parts = []
            
            # Overall performance
            if overall_score >= 8:
                summary_parts.append(f"{candidate.name} demonstrated exceptional performance throughout the interview")
            elif overall_score >= 6:
                summary_parts.append(f"{candidate.name} showed good performance with solid responses")
            elif overall_score >= 4:
                summary_parts.append(f"{candidate.name} provided adequate responses but showed room for improvement")
            else:
                summary_parts.append(f"{candidate.name} struggled throughout the interview with below-average responses")
            
            # Response quality
            if duplicate_responses > 0:
                summary_parts.append(f"However, {duplicate_responses} duplicate responses were detected, indicating potential issues with engagement")
            
            if off_topic_responses > 0:
                summary_parts.append(f"Additionally, {off_topic_responses} off-topic responses suggest difficulties in understanding questions")
            
            # Job fit
            summary_parts.append(f"The candidate's responses were evaluated for the {job.title} position at {job.company}")
            
            return ". ".join(summary_parts) + "."
            
        except Exception as e:
            log_warning(f"Error generating executive summary: {e}")
            return f"Interview completed for {candidate.name} with overall score of {overall_score:.1f}/10"
    
    async def _determine_recommendation(
        self,
        overall_score: float,
        duplicate_responses: int,
        off_topic_responses: int,
        total_responses: int
    ) -> tuple:
        """Determine hiring recommendation"""
        try:
            # Check for disqualifying factors
            if duplicate_responses >= 3 or off_topic_responses >= 3:
                return "Do Not Hire", "Excessive duplicate or off-topic responses indicate lack of engagement"
            
            if total_responses < 5:
                return "Do Not Hire", "Insufficient responses to make an informed decision"
            
            # Score-based recommendation
            if overall_score >= 8.5:
                return "Hire", "Exceptional performance across all evaluation criteria"
            elif overall_score >= 7.0:
                return "Strong Consider", "Strong performance with good demonstration of required skills"
            elif overall_score >= 5.0:
                return "Consider", "Adequate performance with potential for development"
            else:
                return "Do Not Hire", "Below-average performance with significant areas for improvement"
            
        except Exception as e:
            log_warning(f"Error determining recommendation: {e}")
            return "Consider", "Standard evaluation completed"
    
    async def _generate_strengths_weaknesses(
        self,
        responses: List[InterviewResponse]
    ) -> tuple:
        """Generate strengths and weaknesses"""
        try:
            strengths = []
            weaknesses = []
            
            if not responses:
                return strengths, weaknesses
            
            # Analyze response patterns
            high_scores = sum(1 for r in responses if r.overall_score and r.overall_score >= 7)
            low_scores = sum(1 for r in responses if r.overall_score and r.overall_score <= 4)
            
            if high_scores >= len(responses) * 0.6:
                strengths.append("Consistently high-quality responses")
            
            if low_scores >= len(responses) * 0.4:
                weaknesses.append("Multiple low-scoring responses")
            
            # Check for specific strengths
            technical_scores = [r.technical_accuracy_score for r in responses if r.technical_accuracy_score is not None]
            if technical_scores and sum(technical_scores) / len(technical_scores) >= 7:
                strengths.append("Strong technical knowledge and experience")
            
            comm_scores = [r.communication_score for r in responses if r.communication_score is not None]
            if comm_scores and sum(comm_scores) / len(comm_scores) >= 7:
                strengths.append("Clear and professional communication")
            
            # Check for specific weaknesses
            if any(r.is_duplicate for r in responses):
                weaknesses.append("Some duplicate responses detected")
            
            if any(r.is_off_topic for r in responses):
                weaknesses.append("Some off-topic responses")
            
            # Default strengths/weaknesses if none identified
            if not strengths:
                strengths.append("Participated actively in the interview")
            
            if not weaknesses:
                weaknesses.append("Continue developing interview skills")
            
            return strengths, weaknesses
            
        except Exception as e:
            log_warning(f"Error generating strengths/weaknesses: {e}")
            return ["Interview completed"], ["Continue professional development"]
    
    async def _generate_improvement_tips(
        self,
        responses: List[InterviewResponse],
        job: Job
    ) -> List[str]:
        """Generate improvement tips"""
        try:
            tips = []
            
            # Analyze response patterns for improvement areas
            if any(r.is_duplicate for r in responses):
                tips.append("Avoid repeating the same responses to different questions")
            
            if any(r.is_off_topic for r in responses):
                tips.append("Listen carefully to questions and address them directly")
            
            # Check for technical improvement
            technical_scores = [r.technical_accuracy_score for r in responses if r.technical_accuracy_score is not None]
            if technical_scores and sum(technical_scores) / len(technical_scores) < 6:
                tips.append("Provide more specific technical examples and details")
            
            # Check for communication improvement
            comm_scores = [r.communication_score for r in responses if r.communication_score is not None]
            if comm_scores and sum(comm_scores) / len(comm_scores) < 6:
                tips.append("Structure responses more clearly with specific examples")
            
            # General tips
            tips.extend([
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions",
                "Prepare specific examples that demonstrate your skills and experience",
                "Practice explaining technical concepts in simple terms"
            ])
            
            return tips[:5]  # Limit to 5 tips
            
        except Exception as e:
            log_warning(f"Error generating improvement tips: {e}")
            return [
                "Provide more specific examples from your experience",
                "Structure responses more clearly",
                "Address questions more directly"
            ]
    
    async def _generate_key_highlights(
        self,
        responses: List[InterviewResponse]
    ) -> List[str]:
        """Generate key highlights"""
        try:
            highlights = []
            
            if not responses:
                return highlights
            
            # Find highest scoring responses
            high_scoring_responses = [r for r in responses if r.overall_score and r.overall_score >= 8]
            
            if high_scoring_responses:
                highlights.append(f"{len(high_scoring_responses)} exceptional responses demonstrating strong competency")
            
            # Check for specific achievements
            if any(r.technical_accuracy_score and r.technical_accuracy_score >= 8 for r in responses):
                highlights.append("Demonstrated strong technical knowledge and experience")
            
            if any(r.communication_score and r.communication_score >= 8 for r in responses):
                highlights.append("Excellent communication skills and clarity")
            
            return highlights
            
        except Exception as e:
            log_warning(f"Error generating key highlights: {e}")
            return ["Interview completed successfully"]
    
    async def _generate_red_flags(
        self,
        responses: List[InterviewResponse],
        duplicate_responses: int,
        off_topic_responses: int
    ) -> List[str]:
        """Generate red flags"""
        try:
            red_flags = []
            
            if duplicate_responses >= 2:
                red_flags.append(f"{duplicate_responses} duplicate responses detected")
            
            if off_topic_responses >= 2:
                red_flags.append(f"{off_topic_responses} off-topic responses")
            
            # Check for consistently low scores
            if responses:
                low_scores = sum(1 for r in responses if r.overall_score and r.overall_score <= 3)
                if low_scores >= len(responses) * 0.5:
                    red_flags.append("Consistently low performance across multiple responses")
            
            return red_flags
            
        except Exception as e:
            log_warning(f"Error generating red flags: {e}")
            return []
    
    async def _generate_next_steps(
        self,
        recommendation: str,
        overall_score: float
    ) -> List[str]:
        """Generate next steps"""
        try:
            next_steps = []
            
            if recommendation == "Hire":
                next_steps.extend([
                    "Proceed with reference checks",
                    "Schedule final interview with hiring manager",
                    "Prepare offer letter and onboarding plan"
                ])
            elif recommendation == "Strong Consider":
                next_steps.extend([
                    "Conduct additional technical assessment",
                    "Schedule follow-up interview",
                    "Check references"
                ])
            elif recommendation == "Consider":
                next_steps.extend([
                    "Review responses in detail",
                    "Consider additional screening",
                    "Evaluate against other candidates"
                ])
            else:  # Do Not Hire
                next_steps.extend([
                    "Document reasons for rejection",
                    "Provide feedback to candidate if requested",
                    "Continue with other candidates"
                ])
            
            return next_steps
            
        except Exception as e:
            log_warning(f"Error generating next steps: {e}")
            return ["Review interview results", "Make hiring decision"]
    
    async def _generate_interviewer_notes(
        self,
        candidate: Candidate,
        job: Job,
        overall_score: float,
        total_responses: int,
        duplicate_responses: int,
        off_topic_responses: int
    ) -> str:
        """Generate interviewer notes"""
        try:
            notes = []
            
            notes.append(f"Interview completed for {candidate.name} for {job.title} position")
            notes.append(f"Overall score: {overall_score:.1f}/10 based on {total_responses} responses")
            
            if duplicate_responses > 0:
                notes.append(f"Note: {duplicate_responses} duplicate responses detected")
            
            if off_topic_responses > 0:
                notes.append(f"Note: {off_topic_responses} off-topic responses")
            
            if overall_score >= 7:
                notes.append("Candidate demonstrated strong competency and should be considered for next round")
            elif overall_score >= 5:
                notes.append("Candidate showed adequate performance but may need additional assessment")
            else:
                notes.append("Candidate struggled with interview questions and may not be suitable for this role")
            
            return ". ".join(notes) + "."
            
        except Exception as e:
            log_warning(f"Error generating interviewer notes: {e}")
            return f"Interview completed for {candidate.name} with score of {overall_score:.1f}/10"
    
    def _fallback_summary(self) -> Dict:
        """Fallback summary when generation fails"""
        return {
            'executive_summary': 'Interview completed successfully',
            'overall_score': 5.0,
            'recommendation': 'Consider',
            'recommendation_reason': 'Standard evaluation completed',
            'technical_assessment': {'score': 5.0, 'summary': 'Assessment completed'},
            'communication_assessment': {'score': 5.0, 'summary': 'Assessment completed'},
            'cultural_fit': {'score': 5.0, 'summary': 'Assessment completed'},
            'strengths': ['Completed interview'],
            'areas_for_improvement': ['Continue professional development'],
            'key_highlights': ['Interview completed'],
            'red_flags': [],
            'improvement_tips': ['Continue professional development'],
            'next_steps': ['Review interview results'],
            'interviewer_notes': 'Interview completed successfully'
        }
