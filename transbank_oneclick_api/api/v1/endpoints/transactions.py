from fastapi import APIRouter, Depends, Query
from typing import Optional
import structlog

from transbank_oneclick_api.services.transbank_service import TransbankService
from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.schemas.oneclick_schemas import (
    TransactionAuthorizeRequest,
    TransactionAuthorizeResponse,
    TransactionStatusResponse,
    TransactionCaptureRequest,
    TransactionCaptureResponse,
    TransactionRefundRequest,
    TransactionRefundResponse,
    TransactionHistoryResponse
)
from transbank_oneclick_api.schemas.response_models import ApiResponse
from transbank_oneclick_api.core.exceptions import (
    InscriptionNotFoundException,
    OrdenCompraDuplicadaException
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/authorize", response_model=ApiResponse[TransactionAuthorizeResponse])
async def authorize_transaction(
    request: TransactionAuthorizeRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Authorize mall transaction using inscribed card.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service for authorization
    - Return standardized response

    Service handles ALL business logic:
    - Check for duplicate orders
    - Verify inscription exists
    - Call Transbank API
    - Persist transaction
    - Database commit/rollback
    """
    try:
        logger.info("Authorizing transaction endpoint", username=request.username)

        # Service handles all validation, business logic, and DB operations
        result = await transbank_service.authorize_transaction(
            username=request.username,
            buy_order=request.parent_buy_order,
            details=[detail.model_dump() for detail in request.details]
        )

        logger.info(
            "Transaction authorized successfully",
            username=request.username,
            parent_buy_order=request.parent_buy_order
        )

        return ApiResponse.success_response(result)

    except (OrdenCompraDuplicadaException, InscriptionNotFoundException):
        raise
    except Exception as e:
        logger.error(
            "Error authorizing transaction",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/status/{child_buy_order}", response_model=ApiResponse[TransactionStatusResponse])
async def get_transaction_status(
    child_buy_order: str,
    child_commerce_code: str = Query(..., description="Child commerce code"),
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Get transaction status from Transbank.

    Router responsibilities:
    - Validate input
    - Call service
    - Return standardized response

    Service returns Pydantic schema directly.
    """
    try:
        logger.info(
            "Getting transaction status endpoint",
            child_buy_order=child_buy_order,
            child_commerce_code=child_commerce_code
        )

        # Service returns TransactionStatusResponse (Pydantic)
        result = await transbank_service.get_transaction_status(
            child_buy_order=child_buy_order,
            child_commerce_code=child_commerce_code
        )

        logger.info(
            "Transaction status retrieved successfully",
            child_buy_order=child_buy_order
        )

        return ApiResponse.success_response(result)

    except Exception as e:
        logger.error(
            "Error getting transaction status",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.put("/capture", response_model=ApiResponse[TransactionCaptureResponse])
async def capture_transaction(
    request: TransactionCaptureRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Capture deferred transaction.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service
    - Return standardized response

    Service returns Pydantic schema directly.
    """
    try:
        logger.info(
            "Capturing transaction endpoint",
            child_buy_order=request.child_buy_order,
            capture_amount=request.capture_amount
        )

        # Service returns TransactionCaptureResponse (Pydantic)
        result = await transbank_service.capture_transaction(
            child_commerce_code=request.child_commerce_code,
            child_buy_order=request.child_buy_order,
            authorization_code=request.authorization_code,
            capture_amount=request.capture_amount
        )

        logger.info(
            "Transaction captured successfully",
            child_buy_order=request.child_buy_order,
            captured_amount=request.capture_amount
        )

        return ApiResponse.success_response(result)

    except Exception as e:
        logger.error(
            "Error capturing transaction",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.post("/refund", response_model=ApiResponse[TransactionRefundResponse])
async def refund_transaction(
    request: TransactionRefundRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Refund/reverse transaction.

    Router responsibilities:
    - Validate input (Pydantic)
    - Call service
    - Return standardized response

    Service returns Pydantic schema directly.
    """
    try:
        logger.info(
            "Refunding transaction endpoint",
            child_buy_order=request.child_buy_order,
            amount=request.amount
        )

        # Service returns TransactionRefundResponse (Pydantic)
        result = await transbank_service.refund_transaction(
            child_commerce_code=request.child_commerce_code,
            child_buy_order=request.child_buy_order,
            amount=request.amount
        )

        logger.info(
            "Transaction refunded successfully",
            child_buy_order=request.child_buy_order,
            reversed_amount=request.amount
        )

        return ApiResponse.success_response(result)

    except Exception as e:
        logger.error(
            "Error refunding transaction",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise


@router.get("/history/{username}", response_model=ApiResponse[TransactionHistoryResponse])
async def get_transaction_history(
    username: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Get transaction history for a user.

    Router responsibilities:
    - Validate input (Pydantic + Query params)
    - Call service for data retrieval
    - Return standardized response

    Service handles:
    - Repository queries
    - ORM to Pydantic conversion
    - Pagination logic
    - Filtering (start_date, end_date, status)
    """
    try:
        logger.info(
            "Getting transaction history endpoint",
            username=username,
            page=page,
            limit=limit
        )

        # Service handles all data retrieval and conversion
        result = await transbank_service.get_transaction_history(
            username=username,
            start_date=start_date,
            end_date=end_date,
            status=status,
            page=page,
            limit=limit
        )

        logger.info(
            "Retrieved transaction history",
            username=username,
            count=len(result.transactions),
            page=page
        )

        return ApiResponse.success_response(result)

    except Exception as e:
        logger.error(
            "Error getting transaction history",
            username=username,
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True
        )
        raise
