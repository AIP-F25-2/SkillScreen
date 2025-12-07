

import os
import sys
from fastapi import FastAPI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
COMMON_PATH = os.path.join(BACKEND_DIR, "common-service")

if COMMON_PATH not in sys.path:
    sys.path.append(COMMON_PATH)

from db import DBFactory
from controllers.user_controller import router as user_router
from controllers.organization_controller import router as org_router
from controllers.register_controller import router as register_router
from controllers.onboard_controller import router as onboard_router   

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

DBFactory.init()

app = FastAPI(title="User Service")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(org_router)
app.include_router(register_router)
app.include_router(onboard_router)   
