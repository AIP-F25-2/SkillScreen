# app/main.py
from fastapi import FastAPI
from app.config import settings
from app.controllers.analyze_controller import router as analyze_router
from app.helpers.device_select import pick_device
from app.controllers import processed_controller

app = FastAPI(title=settings.APP_NAME)

DEVICE = pick_device()
print("Using device:", DEVICE)

@app.get("/health")
def health():
    return {"ok": True, "app": settings.APP_NAME}

app.include_router(analyze_router, prefix="")
app.include_router(processed_controller.router)

def get_device():
    return DEVICE