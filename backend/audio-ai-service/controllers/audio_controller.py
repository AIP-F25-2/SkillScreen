from fastapi import APIRouter
from schemas.audio_schemas import AnalysisRequest
from services import audio_processing_service

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Audio AI Service is running"}

@router.post("/v1/audio/analyses")
def start_analysis(request: AnalysisRequest):
    # Pass the request data to our service logic
    result = audio_processing_service.process_video_for_analysis(
        video_urls=request.video_urls
    )
    return result