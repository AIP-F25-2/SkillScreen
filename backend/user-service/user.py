from fastapi import FastAPI
import os
from dotenv import load_dotenv
from controllers.organization_controller import router as org_router
from controllers.user_controller import router as user_router
from controllers.register_controller import router as register_router
from db import DBFactory
import sys





sys.path.append("/common-service")

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

DBFactory.init()

app = FastAPI(title="User Service")

app.include_router(org_router)
app.include_router(user_router)
app.include_router(register_router)