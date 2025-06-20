"""Global exception handlers for FastAPI application."""

import uuid
import traceback
from datetime import datetime
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import VMServiceException
from .error_codes import ErrorCode
from .logging import get_logger


logger = get_logger("exception_handler")


async def vm_service_exception_handler(request: Request, exc: VMServiceException) -> JSONResponse:
    """Handle VMServiceException and return standardized error response."""
    
    # Generate request ID if not present
    request_id = getattr(request.state, 'request_id', None)
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Log the error
    logger.error(
        f"VMServiceException: {exc.error_code.value} - {exc.message}",
        extra={
            "error_code": exc.error_code.value,
            "error_category": exc.category.value,
            "request_id": request_id,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return standardized error response
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(request_id)
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException and convert to standardized format."""
    
    request_id = getattr(request.state, 'request_id', None)
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Map HTTP status codes to error codes
    status_to_error_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.RESOURCE_CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        503: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        504: ErrorCode.EXTERNAL_SERVICE_TIMEOUT,
    }
    
    error_code = status_to_error_code.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
    
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code.value,
                "message": str(exc.detail),
                "details": {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors and convert to standardized format."""
    
    request_id = getattr(request.state, 'request_id', None)
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation error: {len(validation_errors)} field(s) failed validation",
        extra={
            "validation_errors": validation_errors,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Request validation failed",
                "details": {
                    "validation_errors": validation_errors
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions and return standardized error response."""
    
    request_id = getattr(request.state, 'request_id', None)
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Log the full exception with traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Don't expose internal error details in production
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "An internal server error occurred",
                "details": {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id
            }
        }
    )


def setup_exception_handlers(app):
    """Set up all exception handlers for the FastAPI application."""
    
    # VMServiceException - our custom exceptions
    app.add_exception_handler(VMServiceException, vm_service_exception_handler)
    
    # FastAPI HTTPException
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured successfully")