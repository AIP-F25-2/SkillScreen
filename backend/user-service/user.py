from fastapi import FastAPI
import os
import sys
from dotenv import load_dotenv

# Ensure common service modules are importable (e.g., db, repository)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
COMMON_SERVICE_PATH = os.path.join(BACKEND_DIR, "common-service")
if COMMON_SERVICE_PATH not in sys.path:
    sys.path.insert(0, COMMON_SERVICE_PATH)

from controllers.user_controller import router as user_router
from db import DBFactory
from repositories.user_repository import users_table, metadata

load_dotenv()

PORT = int(os.getenv("PORT", 8080))

app = FastAPI(title="User Service")

app.include_router(user_router)

# Ensure database and tables are ready on startup
@app.on_event("startup")
def on_startup():
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing database connection...")
        DBFactory.init()
        engine = DBFactory.get_engine()
        
        # Bind metadata to engine and create tables if they don't exist
        logger.info("Creating database tables if they don't exist...")
        metadata.bind = engine
        metadata.create_all(engine)
        logger.info("Database initialization completed successfully")
    except ValueError as e:
        logger.error(f"Database configuration error: {str(e)}")
        logger.warning("Service will continue, but database operations may fail")
    except RuntimeError as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.warning("Service will continue, but database operations may fail")
    except Exception as e:
        logger.error(f"Unexpected error during database startup: {str(e)}", exc_info=True)
        logger.warning("Service will continue, but database operations may fail")
