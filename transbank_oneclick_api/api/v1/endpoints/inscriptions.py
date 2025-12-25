import structlog
from typing import Optional
from fastapi import APIRouter, Depends

from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.core.exceptions import InscriptionNotFoundException
from transbank_oneclick_api.repositories.inscription_repository import \
    InscriptionRepository
from transbank_oneclick_api.schemas.oneclick_schemas import (
    InscriptionDeleteRequest, InscriptionDeleteResponse,
    InscriptionFinishRequest, InscriptionFinishResponse,
    InscriptionListResponse, InscriptionStartRequest, InscriptionStartResponse)
from transbank_oneclick_api.schemas.response_models import ApiResponse
from transbank_oneclick_api.services.transbank_service import TransbankService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/start", response_model=ApiResponse[InscriptionStartResponse])
async def start_inscription(
    request: InscriptionStartRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Start card inscription process.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service
    - Return standardized response
    """
    try:
        logger.info("Starting inscription endpoint", username=request.username)

        # Service returns Pydantic schema and handles all DB operations
        return ApiResponse.success_response(await transbank_service.start_inscription(request))

    except Exception as e:
        logger.error(
            "Error starting inscription",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.put("/finish", response_model=ApiResponse[InscriptionFinishResponse])
async def finish_inscription(
    request: InscriptionFinishRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Finish card inscription process.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service
    - Return standardized response

    NO database operations - Service handles everything.
    """
    return ApiResponse.success_response(await transbank_service.finish_inscription(request))


@router.delete("/delete", response_model=ApiResponse[InscriptionDeleteResponse])
async def delete_inscription(
    request: InscriptionDeleteRequest,
    transbank_service: TransbankService = Depends(get_transbank_service),
    inscription_repo: InscriptionRepository = Depends()
):
    """
    Delete card inscription.

    Router responsibilities:
    - Validate input (Pydantic)
    - Get inscription via repository
    - Call service for deletion
    - Return standardized response

    NO database commit/rollback - Service handles transactions.
    """
    try:
        logger.info("Deleting inscription endpoint", username=request.username)

        # 1. Find inscription (via repository, not direct query)
        inscription = inscription_repo.get_active_by_username(request.username)

        if not inscription:
            raise InscriptionNotFoundException(request.username)

        # 2. Service handles Transbank API call and DB deletion
        await transbank_service.delete_inscription(
            tbk_user=inscription.tbk_user,
            username=request.username
        )

        logger.info("Inscription deleted successfully", username=request.username)

        return ApiResponse.success_response(None)

    except Exception as e:
        logger.error(
            "Error deleting inscription",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/{username}", response_model=ApiResponse[InscriptionListResponse])
async def list_user_inscriptions(
    username: str,
    is_active: Optional[bool] = None,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Get all inscriptions for a user, optionally filtered by active status.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service
    - Return standardized response

    Query parameters:
    - is_active: Optional filter. If True, returns only active inscriptions.
                 If False, returns only inactive inscriptions.
                 If None (default), returns all inscriptions.
    """
    try:
        logger.info("Listing user inscriptions", username=username, is_active=is_active)

        # Service handles repository call and ORM to Pydantic conversion
        return ApiResponse.success_response(
            await transbank_service.list_user_inscriptions(username, is_active)
        )

    except Exception as e:
        logger.error(
            "Error retrieving inscriptions",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise
