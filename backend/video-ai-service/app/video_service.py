# app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from app.utils.config import settings
from app.controllers.analyze_controller import router as analyze_router
from app.controllers import processed_controller
from app.helpers.device_select import pick_device

app = FastAPI(title=settings.APP_NAME)
STATIC_DIR = Path(__file__).resolve().parent / "static"

DEVICE = pick_device()
print("Using device:", DEVICE)

@app.get("/health")
@app.get("/healthz", include_in_schema=False)
def health():
    return {"ok": True, "app": settings.APP_NAME}


@app.get("/video-ai/health", include_in_schema=False)
@app.get("/video/health", include_in_schema=False)
@app.get("/video-ai/healthz", include_in_schema=False)
@app.get("/video/healthz", include_in_schema=False)
def proxy_health():
    """
    Extra aliases so the gateway can probe /video-ai/health or /video/health variants.
    """
    return health()

for _prefix in ("", "/video-ai", "/video"):
    app.include_router(analyze_router, prefix=_prefix)
    app.include_router(processed_controller.router, prefix=_prefix)

def _render_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"message": "Video AI Service running. Add app/static/index.html for the test console."})


@app.get("/", include_in_schema=False)
def index():
    """
    Lightweight test console for manual endpoint validation.
    """
    return _render_index()


@app.get("/video-ai", include_in_schema=False)
@app.get("/video-ai/", include_in_schema=False)
@app.get("/video", include_in_schema=False)
@app.get("/video/", include_in_schema=False)
def prefixed_index():
    """
    Gateway-friendly alias so /video-ai/ returns the same console.
    """
    return _render_index()


def get_device():
    return DEVICE
