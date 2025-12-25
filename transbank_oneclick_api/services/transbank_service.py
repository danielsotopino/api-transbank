from datetime import datetime, timezone
from typing import List, Optional
import structlog
from sqlalchemy.orm import Session
from fastapi import Depends
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction, MallTransactionAuthorizeDetails

from transbank_oneclick_api.domain.entities.inscription import (
    InscriptionEntity,
    InscriptionStatus,
    CardDetails
)
from transbank_oneclick_api.domain.entities.transaction import (
    TransactionEntity,
    TransactionDetail,
    Amount,
    TransactionStatus,
    PaymentType
)

from ..config import settings
from ..database import get_db
from ..repositories.inscription_repository import InscriptionRepository
from ..repositories.transaction_repository import TransactionRepository
from ..schemas.oneclick_schemas import (
    InscriptionFinishRequest,
    InscriptionStartRequest,
    InscriptionStartResponse,
    InscriptionFinishResponse,
    InscriptionListResponse,
    InscriptionInfo,
    TransactionAuthorizeResponse,
    TransactionDetailResponse,
    TransactionStatusResponse,
    TransactionRefundResponse,
    TransactionCaptureResponse
)
from ..core.exceptions import (
    TransbankCommunicationException,
    TransactionRejectedException,
    InscriptionNotFoundException
)

logger = structlog.get_logger(__name__)


class TransbankService:
    """
    Service layer for Transbank Oneclick operations.

    Responsibilities:
    - Business logic and Transbank SDK integration
    - Transaction management (commit/rollback)
    - Converts ORM models to Pydantic schemas
    - Orchestrates repository calls
    """

    mall_inscription: MallInscription
    mall_transaction: MallTransaction

    def __init__(
        self,
        db: Session = Depends(get_db),
        inscription_repo: InscriptionRepository = None,
        transaction_repo: TransactionRepository = None
    ):
        self.db = db
        # Initialize repos with db session if not provided
        if inscription_repo is None:
            inscription_repo = InscriptionRepository(db=db)
        if transaction_repo is None:
            transaction_repo = TransactionRepository(db=db)
        self.inscription_repo = inscription_repo
        self.transaction_repo = transaction_repo
        self._configure_transbank()

    def _configure_transbank(self):
        """Configure Transbank SDK based on environment"""
        if settings.TRANSBANK_ENVIRONMENT == "production":
            self.mall_inscription = MallInscription.build_for_production(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            self.mall_transaction = MallTransaction.build_for_production(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            logger.info("Transbank configured for production")
        else:
            self.mall_inscription = MallInscription.build_for_integration(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            self.mall_transaction = MallTransaction.build_for_integration(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            logger.info("Transbank configured for integration/testing")

    async def start_inscription(
        self,
        request: InscriptionStartRequest
    ) -> InscriptionStartResponse:
        """
        Start card inscription process.

        Args:
            username: User identifier
            email: User email
            response_url: URL for callback

        Returns:
            InscriptionStartResponse: Pydantic schema (NOT ORM model)

        Raises:
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Iniciando proceso de inscripción",
                username=request.username,
                email=request.email,
                response_url=request.response_url
            )

            response = self.mall_inscription.start(
                username=request.username,
                email=request.email,
                response_url=request.response_url
            )

            logger.info(
                "Inscripción iniciada exitosamente",
                username=request.username,
                token_prefix=response["token"][:10]
            )

            return InscriptionStartResponse.model_validate(response)

        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error iniciando inscripción",
                username=request.username,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def finish_inscription(self, request: InscriptionFinishRequest) -> InscriptionFinishResponse:
        """
        Finish card inscription process.

        Args:
            token: Inscription token from start_inscription

        Returns:
            InscriptionFinishResponse: Pydantic schema (NOT ORM model)

        Raises:
            TransactionRejectedException: If Transbank rejects inscription
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Finalizando proceso de inscripción",
                token_prefix=request.token[:10]
            )

            # 1. Call Transbank API
            response = self.mall_inscription.finish(request.token)

            if response["response_code"] != 0:
                raise TransactionRejectedException(
                    response["response_code"],
                    "Inscripción rechazada por Transbank"
                )

            # 2. Create Domain Entity
            card_details = CardDetails(
                card_type=response["card_type"],
                card_number=response["card_number"]
            )

            # Use username as email if it's a valid email, otherwise use a default format
            email = request.username if "@" in request.username else f"{request.username}@example.com"
            
            inscription_entity = InscriptionEntity(
                username=request.username,
                email=email,  # Use username if it's an email, otherwise format it
                tbk_user=response["tbk_user"],
                url_webpay="https://webpay.transbank.cl",  # Default URL since not available in finish response
                status=InscriptionStatus.COMPLETED,
                card_details=card_details,
                authorization_code=response["authorization_code"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            # 3. Save via repository (returns Domain Entity)
            saved_entity = self.inscription_repo.save_entity(inscription_entity)

            # 4. Commit transaction
            self.db.commit()

            logger.info(
                "Inscripción finalizada exitosamente",
                tbk_user_prefix=response["tbk_user"][:10],
                card_type=response["card_type"],
                card_number=response["card_number"]
            )

            # 5. Convert Domain Entity to Pydantic schema
            return InscriptionFinishResponse(
                tbk_user=saved_entity.tbk_user,
                response_code=response["response_code"],
                authorization_code=saved_entity.authorization_code,
                card_type=saved_entity.card_details.card_type if saved_entity.card_details else "",
                card_number=saved_entity.card_details.card_number if saved_entity.card_details else ""
            )

        except (TransactionRejectedException, ValueError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error finalizando inscripción",
                token=request.token,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def delete_inscription(self, tbk_user: str, username: str) -> bool:
        """
        Delete card inscription.

        Args:
            tbk_user: Transbank user token
            username: User identifier

        Returns:
            dict: Deletion confirmation

        Raises:
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Eliminando inscripción",
                username=username,
                tbk_user_prefix=tbk_user[:10]
            )

            # Use entity method to get inscription
            inscription_entity = self.inscription_repo.find_active_by_username_entity(username)

            if not inscription_entity:
                raise InscriptionNotFoundException(username)

            self.mall_inscription.delete(tbk_user, username)

            self.inscription_repo.delete(inscription_entity.id)

            self.db.commit()

            logger.info(
                "Inscripción eliminada exitosamente",
                username=username,
                tbk_user_prefix=tbk_user[:10]
            )

            return True

        except (InscriptionNotFoundException,):
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error eliminando inscripción",
                username=username,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def list_user_inscriptions(
        self,
        username: str,
        is_active: Optional[bool] = None
    ) -> InscriptionListResponse:
        """
        List all inscriptions for a user, optionally filtered by active status.

        Args:
            username: User identifier
            is_active: Optional filter for active status.
                      If True, returns only active inscriptions.
                      If False, returns only inactive inscriptions.
                      If None, returns all inscriptions regardless of status.

        Returns:
            InscriptionListResponse: Pydantic schema with list of inscriptions

        Raises:
            None: This is a read-only operation, no exceptions expected
        """
        try:
            logger.info(
                "Listing user inscriptions",
                username=username,
                is_active=is_active
            )

            # Get inscriptions via repository
            inscriptions_orm = self.inscription_repo.get_all_by_username(username, is_active)

            # Convert ORM to Pydantic
            inscription_list = [
                InscriptionInfo(
                    tbk_user=inscription.tbk_user,
                    card_type=inscription.card_type or "UNKNOWN",
                    card_number=inscription.card_number_masked or "****",
                    inscription_date=inscription.inscription_date,
                    status="active" if inscription.is_active else "inactive",
                    is_default=inscription.is_default or False
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
                total_inscriptions=len(inscription_list),
                is_active=is_active
            )

            return response_data

        except Exception as e:
            logger.error(
                "Error retrieving inscriptions",
                username=username,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise

    async def authorize_transaction(
        self,
        username: str,
        buy_order: str,
        details: List[dict]
    ) -> TransactionAuthorizeResponse:
        """
        Authorize mall transaction.

        Args:
            username: User identifier
            buy_order: Parent buy order
            details: List of transaction details

        Returns:
            TransactionAuthorizeResponse: Pydantic schema with nested details

        Raises:
            InscriptionNotFoundException: If inscription not found
            OrdenCompraDuplicadaException: If buy_order already exists
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Autorizando transacción mall",
                username=username,
                buy_order=buy_order,
                details_count=len(details)
            )

            # 1. Check for duplicate buy_order using Domain Entity
            existing_transaction = self.transaction_repo.find_by_buy_order_entity(buy_order)
            if existing_transaction:
                from ..core.exceptions import OrdenCompraDuplicadaException
                raise OrdenCompraDuplicadaException(buy_order)

            # 2. Verify inscription exists (using Domain Entity)
            inscription_entity = self.inscription_repo.find_active_by_username_entity(username)
            if not inscription_entity:
                raise InscriptionNotFoundException(username)

            # 3. Create transaction details for Transbank SDK
            transaction_details = MallTransactionAuthorizeDetails(
                commerce_code=details[0]["commerce_code"],
                buy_order=buy_order,
                installments_number=0,
                amount=details[0]["amount"]
            )

            # 4. Call Transbank API
            response = self.mall_transaction.authorize(
                username=username,
                tbk_user=inscription_entity.tbk_user,
                parent_buy_order=buy_order,
                details=transaction_details
            )

            logger.debug("Response received from Transbank", response=response)

            # 5. Create Transaction Domain Entity
            transaction_date = datetime.fromisoformat(response.get("transaction_date").replace("Z", "+00:00"))
            
            transaction_entity = TransactionEntity(
                username=username,
                buy_order=buy_order,
                inscription_id=inscription_entity.id,
                card_number=response.get("card_detail", {}).get("card_number"),
                accounting_date=response.get("accounting_date"),
                transaction_date=transaction_date,
                created_at=datetime.now(timezone.utc)
            )

            # 6. Add transaction details to entity
            for detail_dict in response["details"]:
                if detail_dict["response_code"] != 0:
                    logger.warning(
                        "Transacción rechazada para comercio",
                        commerce_code=detail_dict['commerce_code'],
                        response_code=detail_dict["response_code"],
                        buy_order=detail_dict["buy_order"],
                        amount=detail_dict["amount"]
                    )

                # Create TransactionDetail entity
                detail_entity = TransactionDetail(
                    commerce_code=detail_dict["commerce_code"],
                    buy_order=detail_dict["buy_order"],
                    amount=Amount(value=detail_dict["amount"]),
                    status=TransactionStatus.AUTHORIZED if detail_dict["response_code"] == 0 else TransactionStatus.FAILED,
                    authorization_code=detail_dict.get("authorization_code"),
                    payment_type_code=PaymentType(detail_dict["payment_type_code"]) if detail_dict.get("payment_type_code") else None,
                    response_code=detail_dict.get("response_code"),
                    installments_number=detail_dict.get("installments_number")
                )

                transaction_entity.add_detail(detail_entity)

            # 7. Save via repository (converts entity to ORM internally)
            saved_entity = self.transaction_repo.save_entity(transaction_entity)

            # 8. Commit transaction
            self.db.commit()

            logger.info(
                "Transacción autorizada exitosamente",
                username=username,
                buy_order=buy_order,
                approved_count=len(saved_entity.get_authorized_details())
            )

            # 9. Convert Domain Entity to Pydantic schema
            return self._transaction_entity_to_pydantic(saved_entity, session_id=response.get("session_id", ""))

        except (InscriptionNotFoundException, ValueError):
            raise
        except Exception as e:
            # Check if it's already a domain exception
            from ..core.exceptions import DomainException
            if isinstance(e, DomainException):
                raise
            self.db.rollback()
            logger.error(
                "Error autorizando transacción",
                username=username,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def get_transaction_status(
        self,
        child_buy_order: str,
        child_commerce_code: str
    ) -> TransactionStatusResponse:
        """
        Get transaction status.

        Args:
            child_buy_order: Child buy order
            child_commerce_code: Child commerce code

        Returns:
            TransactionStatusResponse: Pydantic schema

        Raises:
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Consultando estado de transacción",
                child_buy_order=child_buy_order,
                child_commerce_code=child_commerce_code
            )

            # Call Transbank API (no DB persistence for status query)
            response = self.mall_transaction.status(
                buy_order=child_buy_order
            )

            # Transform response to Pydantic schema
            # Handle transaction_date - can be datetime object or string (SDK version compatibility)
            # transaction_date = datetime.fromisoformat(response.get("transaction_date").replace("Z", "+00:00"))
            
            result = TransactionStatusResponse(
                buy_order=response["buy_order"],
                session_id=response.get("session_id", ""),
                card_detail=response["card_detail"],
                accounting_date=response["accounting_date"],
                transaction_date=response.get("transaction_date"),
                details=[
                    TransactionDetailResponse(
                        amount=detail["amount"],
                        status="AUTHORIZED" if detail["response_code"] == 0 else "REJECTED",
                        authorization_code=detail["authorization_code"],
                        payment_type_code=detail["payment_type_code"],
                        response_code=detail["response_code"],
                        installments_number=detail["installments_number"],
                        commerce_code=detail["commerce_code"],
                        buy_order=detail["buy_order"]
                    )
                    for detail in response["details"]
                ]
            )

            logger.info(
                "Estado de transacción obtenido exitosamente",
                child_buy_order=child_buy_order
            )

            return result

        except Exception as e:
            logger.error(
                "Error consultando estado de transacción",
                child_buy_order=child_buy_order,
                child_commerce_code=child_commerce_code,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def capture_transaction(
        self,
        child_commerce_code: str,
        child_buy_order: str,
        authorization_code: str,
        capture_amount: int
    ) -> TransactionCaptureResponse:
        """
        Capture deferred transaction.

        Args:
            child_commerce_code: Child commerce code
            child_buy_order: Child buy order
            authorization_code: Authorization code
            capture_amount: Amount to capture

        Returns:
            TransactionCaptureResponse: Pydantic schema

        Raises:
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Capturando transacción diferida",
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                authorization_code=authorization_code,
                capture_amount=capture_amount
            )

            response = self.mall_transaction.capture(
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                authorization_code=authorization_code,
                capture_amount=capture_amount
            )

            result = TransactionCaptureResponse(
                authorization_code=response["authorization_code"],
                authorization_date=response["authorization_date"].isoformat(),
                captured_amount=response["captured_amount"],
                response_code=response["response_code"]
            )

            logger.info(
                "Transacción capturada exitosamente",
                child_buy_order=child_buy_order,
                captured_amount=capture_amount
            )

            return result

        except Exception as e:
            logger.error(
                "Error capturando transacción",
                child_buy_order=child_buy_order,
                capture_amount=capture_amount,
                error_type=type(e).__name__,
                error=str(e)
            )
            raise TransbankCommunicationException(str(e))

    async def refund_transaction(
        self,
        child_commerce_code: str,
        child_buy_order: str,
        amount: int
    ) -> TransactionRefundResponse:
        """
        Refund transaction.

        Args:
            child_commerce_code: Child commerce code
            child_buy_order: Child buy order
            amount: Amount to refund

        Returns:
            TransactionRefundResponse: Pydantic schema

        Raises:
            TransbankCommunicationException: If Transbank API call fails
        """
        try:
            logger.info(
                "Reversando transacción",
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                amount=amount
            )

            response = self.mall_transaction.refund(
                buy_order=child_buy_order,
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                amount=amount
            )

            result = TransactionRefundResponse(
                type=response["type"],
                response_code=response["response_code"],
                reversed_amount=getattr(response, 'reversed_amount', amount)
            )

            logger.info(
                "Transacción reversada exitosamente",
                child_buy_order=child_buy_order,
                reversed_amount=amount
            )

            return result

        except Exception as e:
            logger.error(
                "Error reversando transacción",
                child_buy_order=child_buy_order,
                amount=amount,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    async def get_transaction_history(
        self,
        username: str,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        page: int = 1,
        limit: int = 50
    ):
        """
        Get transaction history for a user.

        Args:
            username: User identifier
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            status: Optional status filter
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            TransactionHistoryResponse: Pydantic schema with transactions and pagination

        Note:
            Currently implements basic pagination.
            TODO: Add date and status filtering in repository layer.
        """
        try:
            from ..schemas.oneclick_schemas import (
                TransactionHistoryResponse,
                TransactionHistoryItem,
                TransactionDetailResponse
            )

            logger.info(
                "Obteniendo historial de transacciones",
                username=username,
                page=page,
                limit=limit
            )

            # Calculate offset
            offset = (page - 1) * limit

            # Get transactions via repository
            transactions_orm = self.transaction_repo.get_by_username(
                username=username,
                skip=offset,
                limit=limit
            )

            # TODO: Apply additional filters (start_date, end_date, status)
            # This should be implemented in the repository layer

            # Convert ORM to Pydantic
            transaction_items = []
            for transaction in transactions_orm:
                detail_responses = [
                    TransactionDetailResponse(
                        amount=detail.amount,
                        status=detail.status,
                        authorization_code=detail.authorization_code,
                        payment_type_code=detail.payment_type_code,
                        response_code=detail.response_code,
                        installments_number=detail.installments_number,
                        commerce_code=detail.commerce_code,
                        buy_order=detail.buy_order,
                        balance=detail.balance
                    )
                    for detail in transaction.details
                ]

                transaction_items.append(
                    TransactionHistoryItem(
                        parent_buy_order=transaction.parent_buy_order,
                        transaction_date=transaction.transaction_date,
                        total_amount=sum(d.amount for d in transaction.details),
                        card_number=transaction.card_number_masked,
                        status=transaction.status,
                        details=detail_responses
                    )
                )

            response_data = TransactionHistoryResponse(
                username=username,
                transactions=transaction_items,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": len(transactions_orm),  # TODO: Get actual total count from repository
                    "total_pages": (len(transactions_orm) + limit - 1) // limit
                }
            )

            logger.info(
                "Historial de transacciones obtenido",
                username=username,
                count=len(transaction_items),
                page=page
            )

            return response_data

        except Exception as e:
            logger.error(
                "Error obteniendo historial de transacciones",
                username=username,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True
            )
            raise TransbankCommunicationException(str(e))

    def _transaction_entity_to_pydantic(
        self,
        entity: TransactionEntity,
        session_id: str = ""
    ) -> TransactionAuthorizeResponse:
        """
        Convert TransactionEntity to Pydantic schema.

        Args:
            entity: TransactionEntity domain entity
            session_id: Session ID from Transbank response

        Returns:
            TransactionAuthorizeResponse: Pydantic schema with nested details
        """
        detail_responses = [
            TransactionDetailResponse(
                buy_order=detail.buy_order,
                commerce_code=detail.commerce_code,
                amount=detail.amount.value,
                status=detail.status.value,
                authorization_code=detail.authorization_code,
                payment_type_code=detail.payment_type_code.value if detail.payment_type_code else None,
                response_code=detail.response_code,
                installments_number=detail.installments_number,
                balance=None  # Not available in domain entity
            )
            for detail in entity.details
        ]
        
        return TransactionAuthorizeResponse(
            parent_buy_order=entity.buy_order,
            session_id=session_id,
            card_detail={"card_number": entity.card_number} if entity.card_number else {},
            accounting_date=entity.accounting_date or "",
            transaction_date=entity.transaction_date,
            details=detail_responses
        )
