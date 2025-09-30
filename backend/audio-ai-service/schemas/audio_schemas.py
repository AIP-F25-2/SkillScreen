from pydantic import BaseModel
from typing import List

class AnalysisRequest(BaseModel):
    video_urls: List[str]