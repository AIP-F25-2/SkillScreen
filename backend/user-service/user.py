from fastapi import FastAPI
import os
from dotenv import load_dotenv
from controllers.user_controller import router as user_router
from db import DBFactory
import sys

sys.path.append("/common-service")

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

DBFactory.init()

app = FastAPI(title="User Service")

app.include_router(user_router)
