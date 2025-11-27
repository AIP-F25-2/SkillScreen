from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from config.logger import logger
from controllers import (
    health_controller,
    resume_controller,
    interview_controller,
    question_controller,
    assessment_controller
)

app = FastAPI(
    title="SkillScreen Orchestration Service",
    description="Single coordination point for all microservices",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_controller.router, tags=["Health"])
app.include_router(resume_controller.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(interview_controller.router, prefix="/api/interviews", tags=["Interviews"])
app.include_router(question_controller.router, prefix="/api/questions", tags=["Questions"])
app.include_router(assessment_controller.router, prefix="/api/assessments", tags=["Assessments"])

@app.on_event("startup")
async def startup():
    logger.info("="*60)
    logger.info(f"🚀 {settings.APP_NAME} Starting")
    logger.info("="*60)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Port: {settings.PORT}")
    logger.info("="*60)

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }
