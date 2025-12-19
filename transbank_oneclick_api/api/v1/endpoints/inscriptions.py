import structlog
from fastapi import APIRouter, Depends

from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.core.exceptions import InscriptionNotFoundException
from transbank_oneclick_api.repositories.inscription_repository import \
    InscriptionRepository
from transbank_oneclick_api.schemas.oneclick_schemas import (
    InscriptionDeleteRequest, InscriptionDeleteResponse,
    InscriptionFinishRequest, InscriptionFinishResponse, InscriptionInfo,
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
    inscription_repo: InscriptionRepository = Depends()
):
    """
    Get all active inscriptions for a user.

    Router responsibilities:
    - Validate input
    - Call repository for data
    - Convert ORM to Pydantic
    - Return standardized response

    Note: This is a read-only operation, so it's acceptable to use repository directly
    without a service layer method.
    """
    try:
        logger.info("Listing user inscriptions", username=username)

        # Get inscriptions via repository
        # For a complete list, we'd need a method like:
        # inscriptions_orm = inscription_repo.get_all_active_by_username(username)
        # For now, using db.query as temporary solution

        # TODO: Add get_all_active_by_username method to InscriptionRepository
        from transbank_oneclick_api.models.oneclick_inscription import \
            OneclickInscription
        db = inscription_repo.db
        inscriptions_orm = db.query(OneclickInscription).filter(
            OneclickInscription.username == username
        ).all()

        # Convert ORM to Pydantic
        inscription_list = [
            InscriptionInfo(
                tbk_user=inscription.tbk_user,
                card_type=inscription.card_type if hasattr(inscription, 'card_type') else "UNKNOWN",
                card_number=inscription.card_number if hasattr(inscription, 'card_number') else "****",
                inscription_date=inscription.created_at,
                status="active",
                is_default=False  # TODO: Implement default card logic
            )
            for inscription in inscriptions_orm
        ]

        response_data = InscriptionListResponse(
            username=username,
            inscriptions=inscription_list,
            total_inscriptions=len(inscription_list)
        )

        logger.info(
            "Retrieved inscriptions",
            username=username,
            total_inscriptions=len(inscription_list)
        )

        return ApiResponse.success_response(response_data)

    except Exception as e:
        logger.error(
            "Error retrieving inscriptions",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise
