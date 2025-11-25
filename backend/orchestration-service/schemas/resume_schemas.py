from pydantic import BaseModel

class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    upload_id: str
    candidates_created: int