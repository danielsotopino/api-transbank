from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar, List

T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """
    Standardized API response format per architecture standards.

    All endpoints must return this format:
    {
        "code": "XX",
        "message": "Human-readable message",
        "data": {...}
    }

    Usage:
        from transbank_oneclick_api.core.response_codes import ResponseCodes

        # Success response
        return StandardResponse(
            code=ResponseCodes.SUCCESS.code,
            message="Inscription started successfully",
            data=result
        )

        # Error response (usually handled by exception handlers)
        return StandardResponse(
            code=ResponseCodes.INSCRIPTION_NOT_FOUND.code,
            message="Inscription not found",
            data=None
        )
    """
    code: str = Field(..., description="Response code (e.g., '00', 'INS_001')")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response payload")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "00",
                "message": "Operation successful",
                "data": {"id": 1, "status": "COMPLETED"}
            }
        }

    @classmethod
    def success_response(cls, data: T, message: str = "Operation successful") -> 'StandardResponse[T]':
        """
        Helper method for creating success responses.

        Args:
            data: Response data
            message: Success message (default: "Operation successful")

        Returns:
            StandardResponse with code "00"
        """
        return cls(code="00", message=message, data=data)

    @classmethod
    def error_response(cls, code: str, message: str, data: Optional[T] = None) -> 'StandardResponse[T]':
        """
        Helper method for creating error responses.

        Args:
            code: Error code (e.g., "INS_001")
            message: Error message
            data: Optional error details

        Returns:
            StandardResponse with error code
        """
        return cls(code=code, message=message, data=data)


# ==================== BACKWARDS COMPATIBILITY ====================
# Alias for backwards compatibility during migration
ApiResponse = StandardResponse


class ApiError(BaseModel):
    """
    DEPRECATED: Use StandardResponse with error code instead.
    Kept for backwards compatibility during migration.
    """
    code: str
    message: str


class LegacyApiResponse(BaseModel, Generic[T]):
    """
    DEPRECATED: Old response format, replaced by StandardResponse.
    Kept for backwards compatibility during migration.

    Old format:
    {
        "success": true,
        "data": {...},
        "errors": [...]
    }
    """
    success: bool
    data: Optional[T] = None
    errors: List[ApiError] = []

    @classmethod
    def success_response(cls, data: T) -> 'LegacyApiResponse[T]':
        """DEPRECATED: Use StandardResponse instead."""
        return cls(success=True, data=data, errors=[])

    @classmethod
    def error_response(cls, errors: List[ApiError]) -> 'LegacyApiResponse[None]':
        """DEPRECATED: Use StandardResponse instead."""
        return cls(success=False, data=None, errors=errors)

    @classmethod
    def single_error(cls, code: str, message: str) -> 'LegacyApiResponse[None]':
        """DEPRECATED: Use StandardResponse instead."""
        return cls.error_response([ApiError(code=code, message=message)])