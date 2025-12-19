# FastAPI 3-Layer Architecture Standards

## Document Purpose
This document establishes the mandatory architecture standards for FastAPI projects, defining clear separation of concerns across Router, Service, and Repository layers with standardized error handling, response formats, proper data flow using Pydantic schemas, and comprehensive logging for observability.

---

## Table of Contents
1. [Router Layer (HTTP Interface)](#1-router-layer-http-interface)
2. [Service Layer (Business Logic)](#2-service-layer-business-logic)
3. [Repository Layer (Data Access)](#3-repository-layer-data-access)
4. [Standardized Response Format](#4-standardized-response-format)
5. [Error Handling System](#5-error-handling-system)
6. [Pydantic Schemas](#6-pydantic-schemas)
7. [Data Flow Architecture](#7-data-flow-architecture)
8. [Logging and Observability](#8-logging-and-observability)
9. [Testing Requirements](#9-testing-requirements)
10. [Architecture Compliance Checklist](#10-architecture-compliance-checklist)
11. [Common Patterns and Examples](#11-common-patterns-and-examples)

---

## 1. ROUTER LAYER (HTTP Interface)

### Responsibilities
- Handle HTTP request/response cycle
- Input validation using Pydantic models
- Dependency injection via `Depends()`
- Delegate business logic to services
- Return standardized responses
- HTTP-specific error handling

### ✅ MUST
- Only handle HTTP concerns (request parsing, response formatting)
- Validate input format with Pydantic models
- Use `Depends()` for service and dependency injection
- Call services for all business logic
- Return standardized response format (see section 4)
- Use exception handlers for error responses
- Document endpoints with proper OpenAPI metadata
- Accept and return **ONLY** Pydantic schemas (never ORM models)

### ❌ MUST NOT
- Contain business logic or validation rules
- Directly access database session or repositories
- Execute `db.commit()` or `db.rollback()`
- Return ORM/SQLAlchemy models directly
- Use try/except for business logic (only for HTTP formatting)
- Perform data transformations (Service layer responsibility)

### Example
```python
# app/routers/user_router.py

import structlog
from fastapi import APIRouter, Depends, status
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.core.responses import StandardResponse
from app.core.response_codes import ResponseCodes
from app.core.logging_decorators import log_function_call

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user"
)
@log_function_call(level="info", include_args=True, exclude_args=["password"])
def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends()
):
    """
    Create a new user.
    
    - **name**: User's full name
    - **email**: Valid email address
    - **password**: At least 8 characters
    
    Possible errors:
    - USR_001 (409): User with email already exists
    - 500: Internal server error
    """
    logger.info("Creating user", email=user_data.email)
    
    # Service returns UserResponse (Pydantic), NOT ORM model
    result = user_service.create_user(user_data)
    
    logger.info("User created successfully", user_id=result.id)
    
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message="User created successfully",
        data=result  # Already a Pydantic schema, safe to return
    )


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    summary="Get user by ID"
)
def get_user(
    user_id: int,
    user_service: UserService = Depends()
):
    """
    Retrieve user information by ID.
    
    Possible errors:
    - USR_002 (404): User not found
    """
    result = user_service.get_user(user_id)
    
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message="User retrieved successfully",
        data=result
    )


@router.get(
    "",
    response_model=StandardResponse[UserListResponse],
    summary="List users with pagination"
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends()
):
    """
    List all active users with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100)
    """
    result = user_service.list_users(skip, limit)
    
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message=f"Retrieved {len(result.users)} users",
        data=result
    )


@router.put(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    summary="Update user information"
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends()
):
    """
    Update user information.
    
    All fields are optional. Only provided fields will be updated.
    
    Possible errors:
    - USR_002 (404): User not found
    - USR_001 (409): Email already exists
    - 500: Internal server error
    """
    result = user_service.update_user(user_id, user_data)
    
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message="User updated successfully",
        data=result
    )


@router.delete(
    "/{user_id}",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user"
)
def delete_user(
    user_id: int,
    user_service: UserService = Depends()
):
    """
    Delete user by ID.
    
    Possible errors:
    - USR_002 (404): User not found
    - 500: Internal server error
    """
    user_service.delete_user(user_id)
    
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message="User deleted successfully"
    )
```

---

## 2. SERVICE LAYER (Business Logic)

### Responsibilities
- Implement all business logic and rules
- Orchestrate operations across multiple repositories
- Manage database transactions
- Business-level validation
- **Convert ORM models to Pydantic schemas**
- Error handling with domain exceptions

### ✅ MUST
- Contain all business logic and validation rules
- Orchestrate calls to multiple repositories when needed
- Handle transactions (`db.commit()`, `db.rollback()`)
- Raise **ONLY** custom `ServiceException` or its subclasses
- Validate business rules (not just data format)
- Receive database session via dependency injection
- Use type hints for all methods
- Log operations and errors appropriately
- **Convert ORM models to Pydantic schemas before returning**
- Accept Pydantic schemas as input parameters

### ❌ MUST NOT
- Know HTTP details (status codes are in ResponseCode definitions)
- Make direct queries with `db.query()` or `db.execute()`
- Import `Request`, `Response` from FastAPI
- Return `JSONResponse` or HTTP-specific objects
- Contain database-specific logic (SQL, ORM queries)
- Raise `HTTPException`
- **Return ORM/SQLAlchemy models directly**

### Example
```python
# app/services/user_service.py

import structlog
from sqlalchemy.orm import Session
from fastapi import Depends
from app.repositories.user_repository import UserRepository
from app.core.exceptions import ConflictError, NotFoundError, ServiceException
from app.core.response_codes import ResponseCodes
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.core.database import get_db
from app.core.security import hash_password
from app.core.logging_decorators import log_function_call

logger = structlog.get_logger(__name__)


class UserService:
    """
    Service layer - Converts ORM models to Pydantic schemas.
    
    CRITICAL: This layer is responsible for:
    1. Converting SQLAlchemy models to Pydantic schemas
    2. Ensuring no sensitive data leaks (passwords, internal fields)
    3. Formatting data for API consumption
    """
    
    def __init__(
        self,
        db: Session = Depends(get_db),
        user_repo: UserRepository = Depends()
    ):
        self.db = db
        self.user_repo = user_repo
    
    @log_function_call(level="info", exclude_args=["password"])
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user.
        
        Args:
            user_data: Pydantic schema with user creation data
            
        Returns:
            UserResponse: Pydantic schema (NOT ORM model)
            
        Raises:
            ConflictError: If user with email already exists
            ServiceException: If database operation fails
        """
        logger.debug("Validating user email", email=user_data.email)
        
        # Business validation
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            logger.warning(
                "User creation failed: email exists",
                email=user_data.email
            )
            raise ConflictError(ResponseCodes.USER_EXISTS)
        
        try:
            logger.debug("Hashing password")
            # Hash password before storing
            hashed_password = hash_password(user_data.password)
            
            # Create user data with hashed password
            user_data_dict = user_data.model_dump()
            user_data_dict['password'] = hashed_password
            
            logger.debug("Creating user in database")
            # Repository returns ORM model
            user_orm = self.user_repo.create(user_data_dict)
            self.db.commit()
            self.db.refresh(user_orm)
            
            logger.info("User created", user_id=user_orm.id)
            
            # Convert ORM model to Pydantic schema
            return UserResponse.model_validate(user_orm)
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "User creation failed",
                error=str(e),
                exc_info=True
            )
            raise ServiceException(
                ResponseCodes.INTERNAL_ERROR,
                custom_message="Failed to create user"
            )
    
    def get_user(self, user_id: int) -> UserResponse:
        """
        Retrieve user by ID.
        
        Returns:
            UserResponse: Pydantic schema with safe fields only
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        # Repository returns ORM model or None
        user_orm = self.user_repo.get_by_id(user_id)
        if not user_orm:
            raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
        
        # Convert to Pydantic (excludes password_hash automatically)
        return UserResponse.model_validate(user_orm)
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> UserListResponse:
        """
        List users with pagination.
        
        Returns:
            UserListResponse: Pydantic schema with user list and metadata
        """
        # Repository returns list of ORM models
        users_orm, total = self.user_repo.list_active(skip, limit)
        
        # Convert each ORM model to Pydantic schema
        users_response = [
            UserResponse.model_validate(user) for user in users_orm
        ]
        
        return UserListResponse(
            users=users_response,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
    
    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ) -> UserResponse:
        """
        Update user information.
        
        Returns:
            UserResponse: Pydantic schema with updated user data
            
        Raises:
            NotFoundError: If user doesn't exist
            ConflictError: If new email already exists
        """
        # Check user exists
        user_orm = self.user_repo.get_by_id(user_id)
        if not user_orm:
            raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
        
        # Check email conflict (if email is being changed)
        if user_data.email and user_data.email != user_orm.email:
            existing = self.user_repo.get_by_email(user_data.email)
            if existing:
                raise ConflictError(ResponseCodes.USER_EXISTS)
        
        # Hash password if being updated
        update_dict = user_data.model_dump(exclude_unset=True)
        if 'password' in update_dict:
            update_dict['password'] = hash_password(update_dict['password'])
        
        try:
            # Repository returns updated ORM model
            updated_user = self.user_repo.update(user_id, update_dict)
            self.db.commit()
            self.db.refresh(updated_user)
            
            logger.info(f"User updated successfully: {user_id}")
            
            # Convert to Pydantic schema
            return UserResponse.model_validate(updated_user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            raise ServiceException(
                ResponseCodes.INTERNAL_ERROR,
                custom_message="Failed to update user"
            )
    
    def delete_user(self, user_id: int) -> None:
        """
        Delete user by ID.
        
        Raises:
            NotFoundError: If user doesn't exist
        """
        user_orm = self.user_repo.get_by_id(user_id)
        if not user_orm:
            raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
        
        try:
            self.user_repo.delete(user_id)
            self.db.commit()
            logger.info(f"User deleted successfully: {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
            raise ServiceException(
                ResponseCodes.INTERNAL_ERROR,
                custom_message="Failed to delete user"
            )
```

---

## 3. REPOSITORY LAYER (Data Access)

### Responsibilities
- Execute database queries and commands
- Provide clean data access interface
- Handle ORM operations
- **Return ORM models or simple data structures**

### ✅ MUST
- Only contain SQL/ORM queries and commands
- Use `db.add()`, `db.query()`, `db.flush()`, `db.delete()`
- **Return ORM models** (let Service layer convert to Pydantic)
- Implement atomic methods (one query per method)
- Receive database session as parameter
- Use type hints for all methods
- Accept simple dictionaries or Pydantic schemas as input

### ❌ MUST NOT
- Execute `db.commit()` or `db.rollback()`
- Contain business logic or validation rules
- Raise `HTTPException` or `ServiceException`
- Know about HTTP or business context
- Convert to Pydantic schemas (Service layer responsibility)

### Example
```python
# app/repositories/user_repository.py

import structlog
from sqlalchemy.orm import Session
from app.models.user import User
from typing import Optional

logger = structlog.get_logger(__name__)


class UserRepository:
    """
    Repository layer - Returns ORM models.
    
    NOTE: This layer returns SQLAlchemy models, NOT Pydantic schemas.
    The service layer is responsible for converting to Pydantic schemas.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: dict) -> User:
        """
        Create a new user record.
        
        Args:
            user_data: Dictionary with user data
            
        Returns:
            User: SQLAlchemy ORM model (NOT Pydantic)
        """
        logger.debug("Inserting user into database", email=user_data.get('email'))
        
        user = User(**user_data)
        self.db.add(user)
        self.db.flush()  # Get ID without committing
        
        logger.debug("User inserted", user_id=user.id)
        
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Returns:
            User | None: SQLAlchemy ORM model or None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email.
        
        Returns:
            User | None: SQLAlchemy ORM model or None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def list_active(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[User], int]:
        """
        List active users with pagination.
        
        Returns:
            tuple: (list of User ORM models, total count)
        """
        query = self.db.query(User).filter(User.is_active == True)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total
    
    def update(self, user_id: int, update_data: dict) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            update_data: Dictionary with fields to update
            
        Returns:
            User | None: Updated SQLAlchemy model or None
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Update only provided fields
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.flush()
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        Delete user by ID.
        
        Returns:
            bool: True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.flush()
        return True
```

---

## 4. STANDARDIZED RESPONSE FORMAT

### Response Structure
All API responses MUST follow this standardized format:

```python
{
    "code": str,      # Traceable response/error code
    "message": str,   # Human-readable message
    "data": Any       # Response payload (optional)
}
```

### Standard Response Codes

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| `00` | Success | 200/201/204 |
| `01` | Bad Request | 400 |
| `401` | Unauthorized | 401 |
| `403` | Forbidden | 403 |
| `404` | Not Found | 404 |
| `409` | Conflict | 409 |
| `500` | Internal Error | 500 |

### Response Schema
```python
# app/core/responses.py

from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standardized API response format."""
    code: str
    message: str
    data: Optional[T] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "00",
                "message": "Operation successful",
                "data": {"id": 1, "name": "Example"}
            }
        }
```

### Response Examples

```python
# Success with data (HTTP 200)
{
    "code": "00",
    "message": "User created successfully",
    "data": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": true,
        "created_at": "2024-12-17T10:00:00Z"
    }
}

# Success without data (HTTP 204)
{
    "code": "00",
    "message": "User deleted successfully"
}

# Bad request (HTTP 400)
{
    "code": "01",
    "message": "Invalid email format"
}

# Not found (HTTP 404)
{
    "code": "USR_002",
    "message": "User not found"
}

# Conflict (HTTP 409)
{
    "code": "USR_001",
    "message": "User with this email already exists"
}

# Internal error (HTTP 500)
{
    "code": "500",
    "message": "An unexpected error occurred"
}
```

---

## 5. ERROR HANDLING SYSTEM

### 5.1 Response Codes Registry

**CRITICAL**: All response codes MUST be registered in a centralized file using `NamedTuple` for immutability and type safety.

#### File: app/core/response_codes.py

```python
# app/core/response_codes.py

from typing import NamedTuple


class ResponseCode(NamedTuple):
    """
    Response code structure with code, message, and HTTP status.
    
    Attributes:
        code: Unique identifier for the response
        message: Default human-readable message
        http_status: HTTP status code to return
    """
    code: str
    message: str
    http_status: int = 200


class ResponseCodes:
    """
    Centralized response code registry.
    
    Format for domain codes: <DOMAIN>_<NUMBER>
    - DOMAIN: 3-letter code identifying the domain (USR, AUTH, ORD, etc.)
    - NUMBER: Sequential 3-digit number (001, 002, etc.)
    
    Usage:
        raise ServiceException(ResponseCodes.USER_EXISTS)
        raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
    """
    
    # ==================== STANDARD CODES ====================
    SUCCESS = ResponseCode("00", "Operation successful", 200)
    BAD_REQUEST = ResponseCode("01", "Invalid request data", 400)
    UNAUTHORIZED = ResponseCode("401", "Authentication required", 401)
    FORBIDDEN = ResponseCode("403", "Access denied", 403)
    NOT_FOUND = ResponseCode("404", "Resource not found", 404)
    CONFLICT = ResponseCode("409", "Resource conflict", 409)
    INTERNAL_ERROR = ResponseCode("500", "Internal server error", 500)
    
    # ==================== USER DOMAIN (USR) ====================
    USER_EXISTS = ResponseCode(
        "USR_001",
        "User with this email already exists",
        409
    )
    USER_NOT_FOUND = ResponseCode(
        "USR_002",
        "User not found",
        404
    )
    USER_INACTIVE = ResponseCode(
        "USR_003",
        "User account is inactive",
        403
    )
    INVALID_PASSWORD = ResponseCode(
        "USR_004",
        "Invalid password format",
        400
    )
    USER_CREATION_FAILED = ResponseCode(
        "USR_005",
        "Failed to create user",
        500
    )
    
    # ==================== AUTHENTICATION DOMAIN (AUTH) ====================
    INVALID_TOKEN = ResponseCode(
        "AUTH_001",
        "Invalid authentication token",
        401
    )
    TOKEN_EXPIRED = ResponseCode(
        "AUTH_002",
        "Authentication token has expired",
        401
    )
    INVALID_CREDENTIALS = ResponseCode(
        "AUTH_003",
        "Invalid username or password",
        401
    )
    SESSION_EXPIRED = ResponseCode(
        "AUTH_004",
        "Session has expired",
        401
    )
    
    # ==================== ORDER DOMAIN (ORD) ====================
    ORDER_NOT_FOUND = ResponseCode(
        "ORD_001",
        "Order not found",
        404
    )
    INSUFFICIENT_STOCK = ResponseCode(
        "ORD_002",
        "Insufficient stock for this product",
        400
    )
    INVALID_ORDER_STATUS = ResponseCode(
        "ORD_003",
        "Invalid order status transition",
        400
    )
    ORDER_ALREADY_CANCELLED = ResponseCode(
        "ORD_004",
        "Order has already been cancelled",
        409
    )
    
    # ==================== PAYMENT DOMAIN (PAY) ====================
    PAYMENT_FAILED = ResponseCode(
        "PAY_001",
        "Payment processing failed",
        402
    )
    INVALID_CARD = ResponseCode(
        "PAY_002",
        "Invalid credit card information",
        400
    )
    INSUFFICIENT_FUNDS = ResponseCode(
        "PAY_003",
        "Insufficient funds",
        402
    )
```

### 5.2 Custom Exception Classes

#### File: app/core/exceptions.py

```python
# app/core/exceptions.py

from app.core.response_codes import ResponseCode


class ServiceException(Exception):
    """
    Base exception for service layer errors.
    
    Automatically extracts code, message, and HTTP status from ResponseCode.
    
    Usage:
        # With default message
        raise ServiceException(ResponseCodes.USER_NOT_FOUND)
        
        # With custom message
        raise ServiceException(
            ResponseCodes.USER_EXISTS,
            custom_message="Email juan@example.com is already registered"
        )
        
        # With additional details
        raise ServiceException(
            ResponseCodes.INVALID_PASSWORD,
            details={
                "requirements": ["8+ chars", "1 uppercase", "1 number"],
                "provided_length": 5
            }
        )
    """
    
    def __init__(
        self,
        response_code: ResponseCode,
        custom_message: str | None = None,
        details: dict | None = None
    ):
        self.code = response_code.code
        self.message = custom_message or response_code.message
        self.http_status = response_code.http_status
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to standardized response format."""
        response = {
            "code": self.code,
            "message": self.message
        }
        if self.details:
            response["details"] = self.details
        return response


class BusinessRuleError(ServiceException):
    """
    Exception for business rule violations (typically 400 errors).
    
    Usage:
        raise BusinessRuleError(ResponseCodes.INSUFFICIENT_STOCK)
    """
    pass


class NotFoundError(ServiceException):
    """
    Exception for resource not found errors (404 errors).
    
    Usage:
        raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
    """
    pass


class ConflictError(ServiceException):
    """
    Exception for resource conflict errors (409 errors).
    
    Usage:
        raise ConflictError(ResponseCodes.USER_EXISTS)
    """
    pass


class AuthenticationError(ServiceException):
    """
    Exception for authentication errors (401 errors).
    
    Usage:
        raise AuthenticationError(ResponseCodes.INVALID_TOKEN)
    """
    pass


class AuthorizationError(ServiceException):
    """
    Exception for authorization errors (403 errors).
    
    Usage:
        raise AuthorizationError(ResponseCodes.FORBIDDEN)
    """
    pass
```

### 5.3 Global Exception Handlers

#### File: app/core/exception_handlers.py

```python
# app/core/exception_handlers.py

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import ServiceException
from app.core.response_codes import ResponseCodes

logger = structlog.get_logger(__name__)


async def service_exception_handler(
    request: Request,
    exc: ServiceException
) -> JSONResponse:
    """
    Handle service layer exceptions.
    
    Automatically converts ServiceException to standardized response format.
    Logs warning-level information for tracking.
    """
    logger.warning(
        f"Service exception: {exc.code} - {exc.message}",
        event="service_exception",
        code=exc.code,
        path=request.url.path,
        method=request.method,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Converts validation errors to standardized format.
    """
    logger.warning(
        f"Validation error on {request.url.path}",
        event="validation_error",
        method=request.method,
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=ResponseCodes.BAD_REQUEST.http_status,
        content={
            "code": ResponseCodes.BAD_REQUEST.code,
            "message": ResponseCodes.BAD_REQUEST.message,
            "details": {"validation_errors": exc.errors()}
        }
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Logs full error details and returns generic error to client.
    """
    logger.error(
        f"Database error on {request.url.path}: {str(exc)}",
        event="database_error",
        exc_info=True,
        method=request.method,
        error_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=ResponseCodes.INTERNAL_ERROR.http_status,
        content={
            "code": ResponseCodes.INTERNAL_ERROR.code,
            "message": "Database error occurred"
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected errors.
    
    Catches all unhandled exceptions to prevent 500 errors without response format.
    """
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        event="unexpected_error",
        exc_info=True,
        method=request.method,
        error_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=ResponseCodes.INTERNAL_ERROR.http_status,
        content={
            "code": ResponseCodes.INTERNAL_ERROR.code,
            "message": ResponseCodes.INTERNAL_ERROR.message
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers to FastAPI app.
    
    Usage in main.py:
        from app.core.exception_handlers import register_exception_handlers
        app = FastAPI()
        register_exception_handlers(app)
    """
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import SQLAlchemyError
    
    app.add_exception_handler(ServiceException, service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

---

## 6. PYDANTIC SCHEMAS

### 6.1 Why Use Pydantic Schemas?

**CRITICAL**: Never return ORM models directly to the API. Always use Pydantic schemas.

#### Problems with returning ORM models:

1. ❌ **Security**: Exposes sensitive fields (passwords, tokens, internal IDs)
2. ❌ **Lazy Loading**: SQLAlchemy relationships may fail outside session
3. ❌ **Unpredictable Serialization**: ORM models don't serialize consistently
4. ❌ **Coupling**: Frontend depends on database structure
5. ❌ **No Control**: Can't filter, transform, or format data

#### Advantages of Pydantic schemas:

1. ✅ **Security**: Only expose safe fields
2. ✅ **Validation**: Automatic data validation
3. ✅ **Documentation**: Auto-generates OpenAPI docs
4. ✅ **Type Safety**: IDE autocomplete and type checking
5. ✅ **Flexibility**: Easy to add computed fields or transformations
6. ✅ **Versioning**: Easy to maintain multiple API versions

### 6.2 Schema Definitions

#### File: app/schemas/user.py

```python
# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """
    Schema for user responses.
    
    IMPORTANT: Does NOT include password or sensitive data.
    This is what gets returned to the API client.
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Allows .model_validate()


class UserWithPassword(UserResponse):
    """
    Schema with password hash (INTERNAL USE ONLY).
    
    WARNING: Never return this schema in API responses.
    Only use for internal authentication logic.
    """
    password_hash: str
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
```

### 6.3 Converting ORM to Pydantic

```python
# ✅ CORRECT: Using model_validate()
user_orm = self.user_repo.get_by_id(user_id)  # Returns User (ORM)
user_response = UserResponse.model_validate(user_orm)  # Converts to Pydantic

# ✅ CORRECT: Converting list
users_orm = self.user_repo.list_active()  # Returns list[User]
users_response = [UserResponse.model_validate(u) for u in users_orm]

# ❌ WRONG: Returning ORM directly
def get_user(self, user_id: int) -> User:  # Don't do this!
    return self.user_repo.get_by_id(user_id)

# ❌ WRONG: Manual dictionary conversion (use model_validate instead)
def get_user(self, user_id: int) -> UserResponse:
    user = self.user_repo.get_by_id(user_id)
    return UserResponse(  # Verbose and error-prone
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
```

---

## 7. DATA FLOW ARCHITECTURE

### 7.1 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         API CLIENT                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP Request (JSON)
                            │ UserCreate (Pydantic)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      ROUTER LAYER                           │
│  - Validates input (Pydantic)                               │
│  - Injects dependencies                                     │
│  - Calls services for business logic                        │
│  - Returns StandardResponse[UserResponse]                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ UserCreate (Pydantic)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                           │
│  - Business logic & validation                              │
│  - Manages transactions (commit/rollback)                   │
│  - Converts Pydantic → dict for repo                        │
│  - Calls repository methods                                 │
│  - Converts ORM models → Pydantic schemas                   │
│  - Raises ServiceException on errors                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ dict / simple types
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                          │
│  - Database queries only                                    │
│  - Returns ORM models (User)                                │
│  - No business logic                                        │
│  - No commit/rollback                                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ SQL / ORM queries
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        DATABASE                             │
│  - PostgreSQL / MySQL / SQLite                              │
└─────────────────────────────────────────────────────────────┘

RETURN PATH:
────────────
Database → Repository (User ORM) → Service (UserResponse Pydantic) 
→ Router (StandardResponse[UserResponse]) → Client (JSON)
```

### 7.2 Layer Responsibilities Summary

| Layer | Input | Output | Responsibilities |
|-------|-------|--------|------------------|
| **Router** | Pydantic schemas | StandardResponse[Pydantic] | HTTP handling, validation, dependency injection |
| **Service** | Pydantic schemas | Pydantic schemas | Business logic, transactions, ORM→Pydantic conversion |
| **Repository** | dict / simple types | ORM models | Database queries, ORM operations |
| **Database** | SQL | ORM models | Data persistence |

---

## 8. LOGGING AND OBSERVABILITY

### 8.1 Logging Architecture

The application uses **structlog** for structured logging with automatic context propagation through `contextvars`. This provides:

- **Structured logs**: JSON format for production, human-readable for development
- **Correlation IDs**: Request tracing across distributed systems
- **Context propagation**: Automatic inclusion of request metadata
- **Sanitization**: Automatic removal of sensitive data
- **Performance tracking**: Execution time for functions and requests

### 8.2 Logging Configuration

#### File: app/core/logging_config.py

```python
# app/core/logging_config.py

import logging
import sys
from typing import Literal

import structlog


def setup_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    json_logs: bool = True,
    service_name: str = "api-service",
    service_version: str = "1.0.0"
):
    """
    Configure structlog for the FastAPI application.
    
    Args:
        log_level: Logging level
        json_logs: Use JSON format (True for production, False for development)
        service_name: Service name for log identification
        service_version: Service version
    """
    
    # Configure standard Python logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Common processors for all environments
    shared_processors = [
        # Add contextvars (correlation_id, endpoint, method)
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add service metadata
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        # Add stack info if requested
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
    ]
    
    if json_logs:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Human-readable output
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Log startup
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured",
        service=service_name,
        version=service_version,
        log_level=log_level,
        json_logs=json_logs
    )
```

### 8.3 Context Variables

Context variables allow automatic propagation of request metadata across async boundaries.

#### File: app/core/logging_context.py

```python
# app/core/logging_context.py

from contextvars import ContextVar
from typing import Optional

# Context variables for request tracing
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)
endpoint_var: ContextVar[Optional[str]] = ContextVar(
    'endpoint',
    default=None
)
method_var: ContextVar[Optional[str]] = ContextVar(
    'method',
    default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar(
    'user_id',
    default=None
)
```

### 8.4 Correlation Middleware

Middleware to automatically capture and propagate correlation IDs and request metadata.

#### File: app/middleware/correlation_middleware.py

```python
# app/middleware/correlation_middleware.py

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_context import (
    correlation_id_var,
    endpoint_var,
    method_var,
    user_id_var
)

logger = structlog.get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request correlation and logging.
    
    - Generates or extracts correlation ID from headers
    - Sets context variables for automatic log enrichment
    - Logs request start and completion
    - Tracks request duration
    - Sanitizes sensitive headers
    """
    
    SENSITIVE_HEADERS = {
        'authorization',
        'x-api-key',
        'cookie',
        'set-cookie',
        'x-access-token',
        'x-refresh-token'
    }
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get(
            "x-correlation-id",
            request.headers.get("correlation-id", str(uuid.uuid4()))
        )
        
        # Extract request metadata
        endpoint = str(request.url.path)
        method = request.method
        
        # Extract user ID if authenticated (from JWT token or session)
        user_id = self._extract_user_id(request)
        
        # Set context variables
        correlation_id_var.set(correlation_id)
        endpoint_var.set(endpoint)
        method_var.set(method)
        if user_id:
            user_id_var.set(user_id)
        
        # Bind context to logger
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            endpoint=endpoint,
            method=method,
            user_id=user_id
        )
        
        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            event="request_started",
            headers=self._sanitize_headers(dict(request.headers)),
            query_params=dict(request.query_params)
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log request completion
            logger.info(
                "Request completed",
                event="request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Add correlation ID to response headers
            response.headers["x-correlation-id"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log request failure
            logger.error(
                "Request failed",
                event="request_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                exc_info=True
            )
            raise
        
        finally:
            # Clear context variables
            structlog.contextvars.clear_contextvars()
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (JWT token, session, etc.)."""
        # TODO: Implement based on your authentication mechanism
        # Example: Extract from JWT token in Authorization header
        return None
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """Sanitize sensitive headers for logging."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
```

### 8.5 Function Logging Decorator

Decorator for automatic function logging with sanitization.

#### File: app/core/logging_decorators.py

```python
# app/core/logging_decorators.py

import inspect
import time
from functools import wraps
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


def log_function_call(
    *,
    level: str = "info",
    include_args: bool = False,
    include_result: bool = False,
    exclude_args: Optional[list[str]] = None
):
    """
    Decorator for automatic function logging.
    
    Features:
    - Logs function start and completion
    - Tracks execution time
    - Sanitizes sensitive data
    - Works with both sync and async functions
    
    Args:
        level: Log level (debug, info, warning, error)
        include_args: Include function arguments in logs
        include_result: Include function result in logs
        exclude_args: List of argument names to exclude from logs
    
    Example:
        @log_function_call(level="info", include_args=True, exclude_args=["password"])
        def create_user(name: str, email: str, password: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = logger.bind(function=func.__name__)
            
            # Prepare log data
            log_kwargs = {}
            if include_args:
                log_kwargs.update(
                    _prepare_args_for_logging(func, args, kwargs, exclude_args)
                )
            
            # Log function start
            _log_start(func_logger, func.__name__, level, log_kwargs)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Prepare result for logging
                log_result = {}
                if include_result:
                    log_result["result"] = _sanitize_for_logging(result)
                
                # Log success
                execution_time = time.time() - start_time
                _log_success(
                    func_logger,
                    func.__name__,
                    level,
                    execution_time,
                    log_result
                )
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = time.time() - start_time
                _log_error(func_logger, func.__name__, execution_time, e)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = logger.bind(function=func.__name__)
            
            # Prepare log data
            log_kwargs = {}
            if include_args:
                log_kwargs.update(
                    _prepare_args_for_logging(func, args, kwargs, exclude_args)
                )
            
            # Log function start
            _log_start(func_logger, func.__name__, level, log_kwargs)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Prepare result for logging
                log_result = {}
                if include_result:
                    log_result["result"] = _sanitize_for_logging(result)
                
                # Log success
                execution_time = time.time() - start_time
                _log_success(
                    func_logger,
                    func.__name__,
                    level,
                    execution_time,
                    log_result
                )
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = time.time() - start_time
                _log_error(func_logger, func.__name__, execution_time, e)
                raise
        
        # Return appropriate wrapper
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def _log_start(func_logger, func_name: str, level: str, log_kwargs: dict):
    """Log function start."""
    getattr(func_logger, level)(
        f"Function {func_name} started",
        event="function_started",
        **log_kwargs
    )


def _log_success(
    func_logger,
    func_name: str,
    level: str,
    execution_time: float,
    log_result: dict
):
    """Log function success."""
    getattr(func_logger, level)(
        f"Function {func_name} completed",
        event="function_completed",
        execution_time_ms=round(execution_time * 1000, 2),
        **log_result
    )


def _log_error(func_logger, func_name: str, execution_time: float, error: Exception):
    """Log function error."""
    func_logger.error(
        f"Function {func_name} failed",
        event="function_failed",
        error_type=type(error).__name__,
        error_message=str(error),
        execution_time_ms=round(execution_time * 1000, 2),
        exc_info=True
    )


def _prepare_args_for_logging(
    func: Callable,
    args: tuple,
    kwargs: dict,
    exclude_args: Optional[list[str]]
) -> dict:
    """Prepare function arguments for logging."""
    exclude_args = exclude_args or []
    log_data = {}
    
    # Get function signature
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    # Map positional args to parameter names
    for i, arg in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            if param_name not in exclude_args and param_name != 'self':
                log_data[param_name] = _sanitize_for_logging(arg)
    
    # Add kwargs
    for k, v in kwargs.items():
        if k not in exclude_args:
            log_data[k] = _sanitize_for_logging(v)
    
    return log_data


def _sanitize_for_logging(data: Any) -> Any:
    """Sanitize data for logging, removing sensitive information."""
    if data is None:
        return None
    
    if isinstance(data, dict):
        return _sanitize_dict(data)
    
    elif isinstance(data, (list, tuple)):
        return [_sanitize_for_logging(item) for item in data]
    
    elif isinstance(data, str):
        # Truncate long strings
        if len(data) > 1000:
            return f"{data[:1000]}... (truncated, length={len(data)})"
        return data
    
    elif hasattr(data, '__dict__'):
        # Handle objects (like Pydantic models, ORM models)
        try:
            # Try to convert to dict
            if hasattr(data, 'model_dump'):  # Pydantic v2
                return _sanitize_dict(data.model_dump())
            elif hasattr(data, 'dict'):  # Pydantic v1
                return _sanitize_dict(data.dict())
            else:
                return _sanitize_dict(vars(data))
        except:
            return str(data)
    
    else:
        return data


def _sanitize_dict(data: dict) -> dict:
    """Sanitize dictionary by removing sensitive fields."""
    SENSITIVE_FIELDS = {
        'password', 'token', 'authorization', 'secret', 'key', 'api_key',
        'access_token', 'refresh_token', 'credit_card', 'ssn', 
        'social_security', 'auth', 'bearer', 'credentials', 'private_key',
        'password_hash', 'salt'
    }
    
    sanitized = {}
    for k, v in data.items():
        # Check if key is sensitive
        if k.lower() in SENSITIVE_FIELDS or 'password' in k.lower():
            sanitized[k] = "***REDACTED***"
        # Recursively sanitize nested structures
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_dict(v)
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [_sanitize_for_logging(item) for item in v]
        else:
            sanitized[k] = v
    
    return sanitized
```

### 8.6 Log Output Examples

#### Development (Human-Readable)
```
2024-12-17T10:30:45.123Z [info     ] Request started        correlation_id=550e8400-e29b-41d4-a716-446655440000 endpoint=/users method=POST
2024-12-17T10:30:45.124Z [info     ] Function create_user started email=john@example.com
2024-12-17T10:30:45.125Z [debug    ] Validating user email  email=john@example.com
2024-12-17T10:30:45.126Z [debug    ] Hashing password
2024-12-17T10:30:45.127Z [debug    ] Creating user in database
2024-12-17T10:30:45.130Z [debug    ] Inserting user into database email=john@example.com
2024-12-17T10:30:45.135Z [debug    ] User inserted          user_id=1
2024-12-17T10:30:45.136Z [info     ] User created           user_id=1
2024-12-17T10:30:45.137Z [info     ] Function create_user completed execution_time_ms=13.45
2024-12-17T10:30:45.138Z [info     ] User created successfully user_id=1
2024-12-17T10:30:45.139Z [info     ] Request completed      correlation_id=550e8400-e29b-41d4-a716-446655440000 status_code=201 duration_ms=16.23
```

#### Production (JSON)
```json
{
  "timestamp": "2024-12-17T10:30:45.123Z",
  "level": "info",
  "event": "request_started",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "endpoint": "/users",
  "method": "POST",
  "filename": "correlation_middleware.py",
  "func_name": "dispatch",
  "lineno": 45
}
```

### 8.7 Best Practices

#### ✅ DO:
- Use correlation IDs for all requests
- Log at appropriate levels (DEBUG for details, INFO for important events, ERROR for failures)
- Include context (user_id, resource_id) in logs
- Use structured logging (key-value pairs, not string interpolation)
- Sanitize sensitive data (passwords, tokens, PII)
- Log business events (user_created, order_placed, payment_processed)
- Include execution time for performance tracking

#### ❌ DON'T:
- Log sensitive data (passwords, tokens, credit cards, SSN)
- Use string concatenation for log messages
- Log at INFO level in hot paths (use DEBUG)
- Include large payloads in logs (truncate or summarize)
- Log in tight loops (aggregate instead)
- Use print() statements (always use logger)

### 8.8 Monitoring and Alerting

#### Critical Logs to Monitor:
```python
# Service failures
logger.error("Service unavailable", service="payment_gateway")

# Security events
logger.warning("Failed login attempt", user_id=user_id, attempts=3)

# Performance degradation
logger.warning("Slow query detected", query_time_ms=5000, threshold_ms=1000)

# Business events
logger.info("High-value order", order_id=order_id, amount=10000)
```

#### Suggested Alerts:
- Error rate > 1% in 5 minutes
- Average response time > 1000ms
- Failed authentication attempts > 10 in 1 minute
- Database connection pool exhausted
- Memory usage > 80%

### 8.9 Application Setup

```python
# app/main.py

from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.middleware.correlation_middleware import CorrelationMiddleware
from app.core.exception_handlers import register_exception_handlers

# Setup logging (before creating FastAPI app)
setup_logging(
    log_level="INFO",
    json_logs=True,  # Set to False for local development
    service_name="api-service",
    service_version="1.0.0"
)

app = FastAPI(title="API Service")

# Add correlation middleware (should be first)
app.add_middleware(CorrelationMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Add other middleware and routers...
```

---

## 9. TESTING REQUIREMENTS

### 9.1 Repository Tests

```python
# tests/repositories/test_user_repository.py

import pytest
from app.repositories.user_repository import UserRepository

def test_create_user(db_session):
    """Test user creation in repository."""
    repo = UserRepository(db_session)
    user_data = {
        "name": "John Doe",
        "email": "john@test.com",
        "password": "hashed_password_123"
    }
    
    user = repo.create(user_data)
    
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@test.com"
    assert user.password == "hashed_password_123"


def test_get_by_email(db_session):
    """Test retrieving user by email."""
    repo = UserRepository(db_session)
    user_data = {"name": "Jane", "email": "jane@test.com", "password": "hash"}
    repo.create(user_data)
    db_session.commit()
    
    found_user = repo.get_by_email("jane@test.com")
    
    assert found_user is not None
    assert found_user.email == "jane@test.com"


def test_get_by_email_not_found(db_session):
    """Test retrieving non-existent user returns None."""
    repo = UserRepository(db_session)
    
    found_user = repo.get_by_email("nonexistent@test.com")
    
    assert found_user is None


def test_list_active_with_pagination(db_session):
    """Test pagination in list_active."""
    repo = UserRepository(db_session)
    
    # Create 5 users
    for i in range(5):
        repo.create({
            "name": f"User {i}",
            "email": f"user{i}@test.com",
            "password": "hash"
        })
    db_session.commit()
    
    # Get first 3 users
    users, total = repo.list_active(skip=0, limit=3)
    
    assert len(users) == 3
    assert total == 5
```

### 9.2 Service Tests

```python
# tests/services/test_user_service.py

import pytest
from unittest.mock import Mock, MagicMock
from app.services.user_service import UserService
from app.core.exceptions import ConflictError, NotFoundError
from app.core.response_codes import ResponseCodes
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User

def test_create_user_success(db_session):
    """Test successful user creation."""
    # Mock repository
    user_repo_mock = Mock()
    user_repo_mock.get_by_email.return_value = None
    
    # Mock ORM model
    mock_user_orm = User(
        id=1,
        name="John",
        email="john@test.com",
        is_active=True
    )
    user_repo_mock.create.return_value = mock_user_orm
    
    # Test service
    service = UserService(db_session, user_repo_mock)
    user_data = UserCreate(name="John", email="john@test.com", password="pass123")
    
    result = service.create_user(user_data)
    
    # Verify result is Pydantic schema
    assert isinstance(result, UserResponse)
    assert result.name == "John"
    assert result.email == "john@test.com"
    db_session.commit.assert_called_once()


def test_create_user_already_exists(db_session):
    """Test creating user with existing email raises ConflictError."""
    user_repo_mock = Mock()
    user_repo_mock.get_by_email.return_value = Mock(id=1)
    
    service = UserService(db_session, user_repo_mock)
    user_data = UserCreate(name="John", email="john@test.com", password="pass123")
    
    with pytest.raises(ConflictError) as exc_info:
        service.create_user(user_data)
    
    assert exc_info.value.code == ResponseCodes.USER_EXISTS.code
    db_session.commit.assert_not_called()


def test_get_user_not_found(db_session):
    """Test getting non-existent user raises NotFoundError."""
    user_repo_mock = Mock()
    user_repo_mock.get_by_id.return_value = None
    
    service = UserService(db_session, user_repo_mock)
    
    with pytest.raises(NotFoundError) as exc_info:
        service.get_user(999)
    
    assert exc_info.value.code == ResponseCodes.USER_NOT_FOUND.code


def test_list_users_converts_to_pydantic(db_session):
    """Test list_users returns Pydantic schemas, not ORM models."""
    user_repo_mock = Mock()
    
    # Mock ORM models
    mock_users = [
        User(id=1, name="User1", email="user1@test.com", is_active=True),
        User(id=2, name="User2", email="user2@test.com", is_active=True)
    ]
    user_repo_mock.list_active.return_value = (mock_users, 2)
    
    service = UserService(db_session, user_repo_mock)
    result = service.list_users(skip=0, limit=10)
    
    # Verify return type
    assert len(result.users) == 2
    assert all(isinstance(u, UserResponse) for u in result.users)
    assert result.total == 2
```

### 9.3 Router Tests

```python
# tests/routers/test_user_router.py

from fastapi.testclient import TestClient
from app.main import app
from app.core.response_codes import ResponseCodes

client = TestClient(app)

def test_create_user_success():
    """Test successful user creation endpoint."""
    response = client.post(
        "/users",
        json={
            "name": "John Doe",
            "email": "john@test.com",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == ResponseCodes.SUCCESS.code
    assert data["message"] == "User created successfully"
    assert "data" in data
    assert data["data"]["name"] == "John Doe"
    assert "password" not in data["data"]  # Verify password not exposed


def test_create_user_already_exists():
    """Test creating user with existing email returns 409."""
    # First create
    client.post(
        "/users",
        json={
            "name": "John Doe",
            "email": "duplicate@test.com",
            "password": "SecurePass123"
        }
    )
    
    # Try duplicate
    response = client.post(
        "/users",
        json={
            "name": "Jane Doe",
            "email": "duplicate@test.com",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ResponseCodes.USER_EXISTS.code


def test_get_user_not_found():
    """Test getting non-existent user returns 404."""
    response = client.get("/users/99999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == ResponseCodes.USER_NOT_FOUND.code


def test_list_users_returns_standardized_response():
    """Test list endpoint returns standardized format."""
    response = client.get("/users?skip=0&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == ResponseCodes.SUCCESS.code
    assert "data" in data
    assert "users" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
```

---

## 10. ARCHITECTURE COMPLIANCE CHECKLIST

### Pre-Deployment Checklist

Before deploying or reviewing code, verify:

#### Router Layer ✅
- [ ] No business logic in routers
- [ ] All dependencies injected via `Depends()`
- [ ] All responses use `StandardResponse` format
- [ ] All responses include proper `code` from `ResponseCodes`
- [ ] No direct database access
- [ ] No `try/except` for business logic (only HTTP formatting)
- [ ] All endpoints documented with OpenAPI docstrings
- [ ] Possible error codes listed in endpoint documentation
- [ ] **Only accepts and returns Pydantic schemas**
- [ ] **Never returns ORM models**
- [ ] Logging implemented with proper decorators

#### Service Layer ✅
- [ ] All business logic in services
- [ ] Services handle `db.commit()` and `db.rollback()`
- [ ] Only raises `ServiceException` or its subclasses
- [ ] Never raises `HTTPException`
- [ ] No HTTP-specific imports (Request, Response, JSONResponse)
- [ ] Properly orchestrates repository calls
- [ ] All exceptions use `ResponseCodes` constants
- [ ] Logging implemented for operations and errors
- [ ] **Converts ORM models to Pydantic schemas before returning**
- [ ] **Never returns ORM models to router**

#### Repository Layer ✅
- [ ] Only database queries and commands
- [ ] No `db.commit()` or `db.rollback()`
- [ ] **Returns ORM models** (not Pydantic schemas)
- [ ] No business logic or validation
- [ ] No exceptions raised (let them bubble up)
- [ ] Methods are atomic (one operation per method)
- [ ] Accepts simple dicts or parameters
- [ ] Logging for database operations

#### Pydantic Schemas ✅
- [ ] All API inputs defined as Pydantic schemas
- [ ] All API outputs defined as Pydantic schemas
- [ ] Response schemas exclude sensitive data
- [ ] Schemas use `model_config = ConfigDict(from_attributes=True)`
- [ ] Create/Update/Response schemas properly separated
- [ ] Proper validation rules (Field, validators)

#### Error Handling ✅
- [ ] All response codes registered in `response_codes.py`
- [ ] Global exception handlers configured in `main.py`
- [ ] Custom exceptions defined and used consistently
- [ ] Error messages are user-friendly
- [ ] Sensitive information not exposed in error messages
- [ ] Proper logging levels used
- [ ] Exception handlers log with structlog

#### Logging ✅
- [ ] Structlog configured with proper processors
- [ ] Correlation middleware added to app
- [ ] Context variables used for request tracking
- [ ] Sensitive data sanitization in place
- [ ] Function decorators used where appropriate
- [ ] Proper log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] JSON logs for production, readable for development
- [ ] All critical paths logged

#### Testing ✅
- [ ] Repository tests cover all CRUD operations
- [ ] Service tests cover business logic and error cases
- [ ] Service tests verify Pydantic conversion
- [ ] Router tests cover HTTP layer and status codes
- [ ] Router tests verify no sensitive data in responses
- [ ] Error scenarios tested with proper response codes
- [ ] Test coverage > 80%

---

## 11. COMMON PATTERNS AND EXAMPLES

### 11.1 Pattern: Complex Business Logic with Multiple Repos

```python
# Service with multiple repository calls
class OrderService:
    @log_function_call(level="info", include_args=True)
    def create_order(self, order_data: OrderCreate) -> OrderResponse:
        """
        Create order with stock validation.
        
        Demonstrates:
        - Multiple repository calls
        - Transaction management
        - ORM to Pydantic conversion
        """
        logger.debug("Validating product exists", product_id=order_data.product_id)
        
        # Validate product exists (returns ORM model)
        product_orm = self.product_repo.get_by_id(order_data.product_id)
        if not product_orm:
            raise NotFoundError(ResponseCodes.ORDER_NOT_FOUND)
        
        # Check stock (business logic)
        if product_orm.stock < order_data.quantity:
            logger.warning(
                "Insufficient stock",
                product_id=order_data.product_id,
                requested=order_data.quantity,
                available=product_orm.stock
            )
            raise BusinessRuleError(
                ResponseCodes.INSUFFICIENT_STOCK,
                details={
                    "requested": order_data.quantity,
                    "available": product_orm.stock
                }
            )
        
        try:
            # Create order (returns ORM model)
            order_orm = self.order_repo.create(order_data.model_dump())
            
            # Update stock
            self.product_repo.decrease_stock(
                order_data.product_id,
                order_data.quantity
            )
            
            # Commit transaction
            self.db.commit()
            self.db.refresh(order_orm)
            
            logger.info("Order created", order_id=order_orm.id)
            
            # Convert ORM to Pydantic before returning
            return OrderResponse.model_validate(order_orm)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating order: {e}", exc_info=True)
            raise ServiceException(ResponseCodes.INTERNAL_ERROR)
```

### 11.2 Pattern: Nested Relationships

```python
# schemas/order.py
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    items: list[OrderItemResponse]  # Nested schema
    total_amount: Decimal
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Service
def get_order_with_items(self, order_id: int) -> OrderResponse:
    """Get order with all items (nested conversion)."""
    logger.debug("Fetching order with items", order_id=order_id)
    
    # Repository returns ORM model with relationships
    order_orm = self.order_repo.get_by_id_with_items(order_id)
    if not order_orm:
        raise NotFoundError(ResponseCodes.ORDER_NOT_FOUND)
    
    # Pydantic automatically converts nested relationships
    return OrderResponse.model_validate(order_orm)
```

### 11.3 Pattern: Computed Fields

```python
# schemas/user.py
from pydantic import computed_field

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    @computed_field
    @property
    def full_name(self) -> str:
        """Computed field - not in database."""
        return f"{self.first_name} {self.last_name}"
    
    @computed_field
    @property
    def account_age_days(self) -> int:
        """Calculate account age."""
        return (datetime.now() - self.created_at).days
    
    model_config = ConfigDict(from_attributes=True)
```

### 11.4 Pattern: Filtering and Searching

```python
# schemas/user.py
class UserFilter(BaseModel):
    """Schema for filtering users."""
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None


# Service
def search_users(
    self,
    filters: UserFilter,
    skip: int = 0,
    limit: int = 100
) -> UserListResponse:
    """Search users with filters."""
    logger.info("Searching users", filters=filters.model_dump(exclude_unset=True))
    
    # Repository returns ORM models
    users_orm, total = self.user_repo.search(
        filters.model_dump(exclude_unset=True),
        skip,
        limit
    )
    
    # Convert to Pydantic
    users_response = [
        UserResponse.model_validate(u) for u in users_orm
    ]
    
    logger.info("Users found", count=len(users_response), total=total)
    
    return UserListResponse(
        users=users_response,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


# Router
@router.post("/users/search", response_model=StandardResponse[UserListResponse])
def search_users(
    filters: UserFilter,
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends()
):
    """Search users with filters."""
    result = service.search_users(filters, skip, limit)
    return StandardResponse(
        code=ResponseCodes.SUCCESS.code,
        message=f"Found {result.total} users",
        data=result
    )
```

---

## 12. QUICK REFERENCE

### Data Flow Summary

```
CLIENT (JSON)
    ↓
ROUTER (Pydantic Schema)
    ↓
SERVICE (Pydantic Schema)
    ↓
REPOSITORY (ORM Model)
    ↓
DATABASE

RETURN:
DATABASE → REPOSITORY (ORM) → SERVICE (Pydantic) → ROUTER (Pydantic) → CLIENT (JSON)
```

### Layer Responsibilities

```
┌─────────────┬──────────────────────┬─────────────────┬──────────────────┐
│   LAYER     │   INPUT              │   OUTPUT        │   MUST NOT       │
├─────────────┼──────────────────────┼─────────────────┼──────────────────┤
│ ROUTER      │ Pydantic schemas     │ StandardResponse│ Business logic   │
│             │                      │ [Pydantic]      │ DB access        │
│             │                      │                 │ Return ORM       │
├─────────────┼──────────────────────┼─────────────────┼──────────────────┤
│ SERVICE     │ Pydantic schemas     │ Pydantic schemas│ HTTP concerns    │
│             │                      │                 │ Direct queries   │
│             │                      │                 │ Return ORM       │
├─────────────┼──────────────────────┼─────────────────┼──────────────────┤
│ REPOSITORY  │ dict / simple types  │ ORM models      │ Commit/rollback  │
│             │                      │                 │ Business logic   │
│             │                      │                 │ Return Pydantic  │
└─────────────┴──────────────────────┴─────────────────┴──────────────────┘
```

### Response Format Template

```python
{
  "code": "XX",           # From ResponseCodes
  "message": "...",       # Human-readable
  "data": {...}          # Pydantic schema (optional)
}
```

### Exception Usage

```python
# Standard exceptions
raise ServiceException(ResponseCodes.INTERNAL_ERROR)
raise NotFoundError(ResponseCodes.USER_NOT_FOUND)
raise ConflictError(ResponseCodes.USER_EXISTS)
raise BusinessRuleError(ResponseCodes.INSUFFICIENT_STOCK)

# With custom message
raise ServiceException(
    ResponseCodes.USER_EXISTS,
    custom_message="Email john@example.com already registered"
)

# With details
raise ServiceException(
    ResponseCodes.INVALID_PASSWORD,
    details={"min_length": 8, "provided": 5}
)
```

### Pydantic Conversion

```python
# ORM → Pydantic (Service layer)
user_orm: User = self.user_repo.get_by_id(user_id)
user_response: UserResponse = UserResponse.model_validate(user_orm)

# Pydantic → dict (for Repository)
user_data: UserCreate = ...
user_dict: dict = user_data.model_dump()

# List conversion
users_orm: list[User] = self.user_repo.list_active()
users_response: list[UserResponse] = [
    UserResponse.model_validate(u) for u in users_orm
]
```

### Logging Usage

```python
# Import logger
import structlog
logger = structlog.get_logger(__name__)

# Basic logging
logger.info("User created", user_id=user.id)
logger.debug("Processing request", data=request_data)
logger.error("Operation failed", error=str(e), exc_info=True)

# Function decorator
@log_function_call(level="info", include_args=True, exclude_args=["password"])
def create_user(name: str, email: str, password: str):
    ...

# Correlation ID is automatically included in all logs
```

---

## Document Metadata

**Version**: 3.0  
**Last Updated**: 2024-12-17  
**Status**: Active  
**Authors**: Engineering Team  
**Review Cycle**: Quarterly

**Change Log**:
- v3.0 (2024-12-17): Added comprehensive Pydantic schemas section, data flow architecture, and logging/observability section
- v2.0 (2024-12-17): Changed ErrorCodes to ResponseCodes, improved exception system
- v1.0 (2024-12-01): Initial version

---
