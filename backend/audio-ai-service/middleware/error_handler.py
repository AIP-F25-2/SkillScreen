from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from config import logger
import traceback


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "failed",
            "message": "Request validation failed",
            "errors": errors
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    error_id = id(exc)  # Simple error tracking ID
    
    logger.error(
        f"Unhandled exception [ID: {error_id}]: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "failed",
            "message": "Internal server error",
            "error_id": error_id,
            "detail": str(exc) if logger.level == "DEBUG" else "An unexpected error occurred"
        }
    )