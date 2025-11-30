from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from config import logger
from datetime import datetime


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"⚠️ Validation error: {errors}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "data": {
                "details": errors
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "data": {
                "message": str(exc)
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
