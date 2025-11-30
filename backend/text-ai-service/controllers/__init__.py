from .health_controller import router as health_router
from .interview_controller import router as interview_router
from .question_controller import router as question_router

__all__ = ["health_router", "interview_router", "question_router"]
