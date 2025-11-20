from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from config import settings, logger
from controllers.health_controller import router as health_router
from controllers.audio_controller import router as audio_router
from controllers.test_controller import router as test_router
from middleware.error_handler import validation_exception_handler, general_exception_handler
from controllers.tts_controller import router as tts_router
from controllers.streaming_controller import router as streaming_router
from controllers.metrics_controller import router as metrics_router
import warnings


# Suppress specific warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
warnings.filterwarnings("ignore", category=UserWarning, module="speechbrain")
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*")
warnings.filterwarnings("ignore", message=".*MPEG_LAYER_III.*")

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Whisper model: {settings.WHISPER_MODEL_SIZE}")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(audio_router, prefix="/api/audio", tags=["Audio Processing"])
app.include_router(test_router, prefix="/api/test", tags=["Testing & Debug"])
app.include_router(tts_router, prefix="/api/tts", tags=["Text-to-Speech"])
app.include_router(streaming_router, prefix="/api/stream", tags=["Streaming"])
app.include_router(metrics_router, tags=["Metrics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "audio-ai:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )