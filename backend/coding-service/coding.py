import os
import sys
from fastapi import FastAPI
from dotenv import load_dotenv
from controllers.coding_controller import router as coding_router

# allow imports from common-service (for logger, shared stuff)
sys.path.append("/common-service")

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

app = FastAPI(title="Coding Service")

# register routes
app.include_router(coding_router)