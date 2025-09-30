# Audio AI Service

from fastapi import FastAPI
from controllers import audio_controller


app = FastAPI()

app.include_router(audio_controller.router)