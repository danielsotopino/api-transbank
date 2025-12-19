import structlog
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .exceptions import DomainException

logger = structlog.get_logger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Handle domain layer exceptions.

    Converts DomainException to StandardResponse format.
    """
    logger.warning(
        "Domain exception occurred",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.details if exc.details else None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=str(exc.detail),
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": str(exc.status_code),
            "message": str(exc.detail),
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    validation_errors = exc.errors()

    logger.warning(
        "Validation error occurred",
        path=request.url.path,
        method=request.method,
        validation_errors=validation_errors
    )

    # Format validation errors for response
    error_details = []
    for error in validation_errors:
        field_name = '.'.join(str(x) for x in error['loc']) if error['loc'] else 'unknown'
        error_details.append({
            "field": field_name,
            "message": error['msg'],
            "type": error['type']
        })

    return JSONResponse(
        status_code=422,
        content={
            "code": "01",  # BAD_REQUEST code
            "message": "Invalid request data",
            "data": {"validation_errors": error_details}
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(
        "Unexpected error occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": "500",  # INTERNAL_ERROR code
            "message": "Internal server error",
            "data": None
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers"""
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)