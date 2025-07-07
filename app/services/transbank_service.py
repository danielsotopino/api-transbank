from typing import List, Dict, Any
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction
from transbank.webpay.oneclick.mall_transaction import MallTransactionAuthorizeDetails
from ..config import settings
from ..core.structured_logger import StructuredLogger
from ..core.exceptions import (
    TransbankCommunicationException,
    TransaccionRechazadaException,
    TokenExpiradoException
)

logger = StructuredLogger(__name__)


class TransbankService:
    def __init__(self):
        self._configure_transbank()
    
    def _configure_transbank(self):
        """Configure Transbank SDK based on environment"""
        if settings.TRANSBANK_ENVIRONMENT == "production":
            
            MallInscription.build_for_production(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            logger.info("Transbank configured for production")
        else:
            MallInscription.build_for_integration(
                commerce_code=settings.TRANSBANK_COMMERCE_CODE,
                api_key=settings.TRANSBANK_API_KEY
            )
            logger.info("Transbank configured for integration/testing")
    
    async def start_inscription(self, username: str, email: str, response_url: str) -> Dict[str, Any]:
        """Start card inscription process"""
        try:
            logger.with_username(username).info(
                "Iniciando proceso de inscripción",
                {"email": email, "response_url": response_url}
            )
            
            response = MallInscription.start(
                username=username,
                email=email,
                response_url=response_url
            )
            
            result = {
                "token": response.token,
                "url_webpay": response.url_webpay
            }
            
            logger.with_username(username).info(
                "Inscripción iniciada exitosamente",
                {"token": response.token[:10] + "..."}
            )
            
            return result
            
        except Exception as e:
            logger.with_username(username).error(
                f"Error iniciando inscripción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def finish_inscription(self, token: str) -> Dict[str, Any]:
        """Finish card inscription process"""
        try:
            logger.info(
                "Finalizando proceso de inscripción",
                {"token": token[:10] + "..."}
            )
            
            response = MallInscription.finish(token=token)
            
            if response.response_code != 0:
                raise TransaccionRechazadaException(
                    response.response_code,
                    "Inscripción rechazada por Transbank"
                )
            
            result = {
                "tbk_user": response.tbk_user,
                "response_code": response.response_code,
                "authorization_code": response.authorization_code,
                "card_type": response.card_type,
                "card_number": response.card_number
            }
            
            logger.info(
                "Inscripción finalizada exitosamente",
                {
                    "tbk_user": response.tbk_user[:10] + "...",
                    "card_type": response.card_type,
                    "card_number": response.card_number
                }
            )
            
            return result
            
        except TransaccionRechazadaException:
            raise
        except Exception as e:
            logger.error(
                f"Error finalizando inscripción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def delete_inscription(self, tbk_user: str, username: str) -> Dict[str, Any]:
        """Delete card inscription"""
        try:
            logger.with_username(username).info(
                "Eliminando inscripción",
                {"tbk_user": tbk_user[:10] + "..."}
            )
            
            response = MallInscription.delete(
                tbk_user=tbk_user,
                username=username
            )
            
            logger.with_username(username).info(
                "Inscripción eliminada exitosamente",
                {"tbk_user": tbk_user[:10] + "..."}
            )
            
            return {"deleted": True}
            
        except Exception as e:
            logger.with_username(username).error(
                f"Error eliminando inscripción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def authorize_transaction(
        self,
        username: str,
        tbk_user: str,
        parent_buy_order: str,
        details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Authorize mall transaction"""
        try:
            logger.with_username(username).info(
                "Autorizando transacción mall",
                {
                    "parent_buy_order": parent_buy_order,
                    "tbk_user": tbk_user[:10] + "...",
                    "details_count": len(details)
                }
            )
            
            # Create transaction details
            transaction_details = []
            for detail in details:
                transaction_details.append(
                    MallTransactionAuthorizeDetails(
                        commerce_code=detail["commerce_code"],
                        buy_order=detail["buy_order"],
                        installments_number=detail.get("installments_number", 1),
                        amount=detail["amount"]
                    )
                )
            
            response = MallTransaction.authorize(
                username=username,
                tbk_user=tbk_user,
                parent_buy_order=parent_buy_order,
                details=transaction_details
            )
            
            # Process response details
            result_details = []
            for detail in response.details:
                if detail.response_code != 0:
                    logger.with_username(username).warning(
                        f"Transacción rechazada para comercio {detail.commerce_code}",
                        {
                            "response_code": detail.response_code,
                            "buy_order": detail.buy_order,
                            "amount": detail.amount
                        }
                    )
                
                result_details.append({
                    "amount": detail.amount,
                    "status": "approved" if detail.response_code == 0 else "rejected",
                    "authorization_code": detail.authorization_code,
                    "payment_type_code": detail.payment_type_code,
                    "response_code": detail.response_code,
                    "installments_number": detail.installments_number,
                    "commerce_code": detail.commerce_code,
                    "buy_order": detail.buy_order
                })
            
            result = {
                "parent_buy_order": response.parent_buy_order,
                "session_id": response.session_id,
                "card_detail": {
                    "card_number": response.card_detail.card_number
                },
                "accounting_date": response.accounting_date,
                "transaction_date": response.transaction_date.isoformat(),
                "details": result_details
            }
            
            logger.with_username(username).info(
                "Transacción autorizada exitosamente",
                {
                    "parent_buy_order": parent_buy_order,
                    "session_id": response.session_id,
                    "approved_count": len([d for d in result_details if d["status"] == "approved"])
                }
            )
            
            return result
            
        except Exception as e:
            logger.with_username(username).error(
                f"Error autorizando transacción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def get_transaction_status(
        self,
        child_buy_order: str,
        child_commerce_code: str
    ) -> Dict[str, Any]:
        """Get transaction status"""
        try:
            logger.info(
                "Consultando estado de transacción",
                {
                    "child_buy_order": child_buy_order,
                    "child_commerce_code": child_commerce_code
                }
            )
            
            response = MallTransaction.status(
                child_buy_order=child_buy_order,
                child_commerce_code=child_commerce_code
            )
            
            result = {
                "buy_order": response.buy_order,
                "session_id": response.session_id,
                "card_detail": {
                    "card_number": response.card_detail.card_number
                },
                "accounting_date": response.accounting_date,
                "transaction_date": response.transaction_date.isoformat(),
                "details": [{
                    "amount": detail.amount,
                    "status": "approved" if detail.response_code == 0 else "rejected",
                    "authorization_code": detail.authorization_code,
                    "payment_type_code": detail.payment_type_code,
                    "response_code": detail.response_code,
                    "installments_number": detail.installments_number,
                    "commerce_code": detail.commerce_code,
                    "buy_order": detail.buy_order,
                    "balance": getattr(detail, 'balance', None)
                } for detail in response.details]
            }
            
            logger.info(
                "Estado de transacción obtenido exitosamente",
                {"child_buy_order": child_buy_order}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error consultando estado de transacción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def capture_transaction(
        self,
        child_commerce_code: str,
        child_buy_order: str,
        authorization_code: str,
        capture_amount: int
    ) -> Dict[str, Any]:
        """Capture deferred transaction"""
        try:
            logger.info(
                "Capturando transacción diferida",
                {
                    "child_commerce_code": child_commerce_code,
                    "child_buy_order": child_buy_order,
                    "authorization_code": authorization_code,
                    "capture_amount": capture_amount
                }
            )
            
            response = MallTransaction.capture(
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                authorization_code=authorization_code,
                capture_amount=capture_amount
            )
            
            result = {
                "authorization_code": response.authorization_code,
                "authorization_date": response.authorization_date.isoformat(),
                "captured_amount": response.captured_amount,
                "response_code": response.response_code
            }
            
            logger.info(
                "Transacción capturada exitosamente",
                {"child_buy_order": child_buy_order, "captured_amount": capture_amount}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error capturando transacción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def refund_transaction(
        self,
        child_commerce_code: str,
        child_buy_order: str,
        amount: int
    ) -> Dict[str, Any]:
        """Refund transaction"""
        try:
            logger.info(
                "Reversando transacción",
                {
                    "child_commerce_code": child_commerce_code,
                    "child_buy_order": child_buy_order,
                    "amount": amount
                }
            )
            
            response = MallTransaction.refund(
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                amount=amount
            )
            
            result = {
                "type": response.type,
                "response_code": response.response_code,
                "reversed_amount": getattr(response, 'reversed_amount', amount)
            }
            
            logger.info(
                "Transacción reversada exitosamente",
                {"child_buy_order": child_buy_order, "reversed_amount": amount}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error reversando transacción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))