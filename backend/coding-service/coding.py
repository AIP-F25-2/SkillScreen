import os
import sys

# CRITICAL: Set up paths BEFORE any imports that might need them
# allow imports from common-service (for logger, shared stuff)
sys.path.append("/common-service")

# allow imports from text-service (for EnhancedLLMService)
# In Docker, text-service is mounted at /app/text-service
text_service_path = "/app/text-service"
if os.path.exists(text_service_path) and text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

# Now import after paths are set up
from fastapi import FastAPI
from dotenv import load_dotenv
from controllers.coding_controller import router as coding_router

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

app = FastAPI(title="Coding Service")

# register routes
app.include_router(coding_router)