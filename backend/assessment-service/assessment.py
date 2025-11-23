from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, status
from contextlib import asynccontextmanager
from config.settings import settings
from config.logger import logger
from controllers.assessment_controller import router as assessment_router
from controllers.health_controller import router as health_router
from scheduler.scheduler import assessment_scheduler
import uvicorn
import traceback


# ==========================================
# LIFESPAN EVENTS (Startup/Shutdown)
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print(f"\n{'='*60}")
    print(f"🚀 Starting {settings.service_name}")
    print(f"{'='*60}")
    print(f"Environment: {settings.environment}")
    print(f"Port: {settings.service_port}")
    print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    print(f"LLM Model: {settings.groq_model}")
    print(f"Assessment Check Interval: {settings.assessment_check_interval_minutes} minutes")
    print(f"Grace Period: {settings.assessment_grace_period_minutes} minutes")
    print(f"{'='*60}\n")
    
    # Start the assessment scheduler
    assessment_scheduler.start()
    
    yield
    
    # Shutdown
    print(f"\n{'='*60}")
    print(f"🛑 Shutting down {settings.service_name}")
    print(f"{'='*60}\n")
    
    # Stop the scheduler
    assessment_scheduler.stop()


# ==========================================
# CREATE FASTAPI APP
# ==========================================

app = FastAPI(
    title="SkillScreen Assessment Orchestration Service",
    description="""
    Assessment Orchestration Service aggregates AI analysis results from multiple services 
    (audio, video, text, coding) and generates comprehensive candidate assessments with 
    LLM-based recommendations.
    
    ## Features
    - **Intelligent Scheduled Checks**: Runs every night at 2am to detect completed interviews
    - **Multi-Service Score Aggregation**: Combines audio, video, text, and coding analysis
    - **LLM-Based Weight Determination**: Uses Groq API to determine optimal scoring weights
    - **LLM-Based Recommendations**: Generates hire/no-hire recommendations with reasoning
    - **Evidence Linking**: Aggregates evidence across all modalities
    - **Flexible Scoring**: Supports custom weight overrides via API
    
    ## Default Scoring Weights
    **With Coding:**
    - Coding: 40%
    - Text: 20%
    - Audio: 20%
    - Video: 20%
    
    **Without Coding:**
    - Text: 34%
    - Audio: 33%
    - Video: 33%
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ==========================================
# GLOBAL EXCEPTION HANDLER
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions with full traceback"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# ==========================================
# CORS MIDDLEWARE
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REGISTER ROUTERS
# ==========================================

# Health checks
app.include_router(health_router)

# Assessment operations
app.include_router(assessment_router)


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "scheduler": {
            "interval_minutes": settings.assessment_check_interval_minutes,
            "grace_period_minutes": settings.assessment_grace_period_minutes
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "assessment_api": "/v1/assessment",
            "scheduler_status": "/v1/scheduler/status"
        }
    }


# ==========================================
# RUN SERVER (for local development)
# ==========================================

if __name__ == "__main__":
    uvicorn.run(
        "assessment:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,  # Enable auto-reload for development
        log_level=settings.log_level.lower()
    )