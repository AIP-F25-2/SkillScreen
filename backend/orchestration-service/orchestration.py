from fastapi import FastAPI
import os
from dotenv import load_dotenv
from controllers.orchestration_controller import router as orchestration_router
from db import DBFactory
import sys

sys.path.append("/common-service")

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

DBFactory.init()

app = FastAPI(title="Orchestration Service")

app.include_router(orchestration_router)
