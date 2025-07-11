from typing import List, Dict, Any
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction, MallTransactionAuthorizeDetails
from ..config import settings
from ..core.structured_logger import StructuredLogger
from ..core.exceptions import (
    TransbankCommunicationException,
    TransactionRejectedException
)

logger = StructuredLogger(__name__)


class TransbankService:

    mall_inscription: MallInscription
    mall_transaction: MallTransaction

    def __init__(self):
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
    
    async def start_inscription(self, username: str, email: str, response_url: str) -> Dict[str, Any]:
        """Start card inscription process"""
        try:
            logger.with_contexts(username=username, email=email, response_url=response_url).info(
                "Iniciando proceso de inscripción"
            )
            
            response = self.mall_inscription.start(
                username=username,
                email=email,
                response_url=response_url
            )

            logger.info(f"Response: {response}")
            
            result = {
                "token": response["token"],
                "url_webpay": response["url_webpay"]
            }
            
            logger.with_contexts(username=username, token=response["token"][:10] + "...").info(
                "Inscripción iniciada exitosamente"
            )
            
            return result
            
        except Exception as e:
            logger.with_contexts(username=username).error(
                f"Error iniciando inscripción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def finish_inscription(self, token: str) -> Dict[str, Any]:
        """Finish card inscription process"""
        try:
            logger.with_contexts(token=token[:10] + "...").info(
                "Finalizando proceso de inscripción"
            )
            
            response = self.mall_inscription.finish(token)
            
            if response["response_code"] != 0:
                raise TransactionRejectedException(
                    response["response_code"],
                    "Inscripción rechazada por Transbank"
                )
            
            result = {
                "tbk_user": response["tbk_user"],
                "response_code": response["response_code"],
                "authorization_code": response["authorization_code"],
                "card_type": response["card_type"],
                "card_number": response["card_number"]
            }
            
            logger.with_contexts(
                tbk_user=response["tbk_user"][:10] + "...",
                card_type=response["card_type"],
                card_number=response["card_number"]
            ).info(
                "Inscripción finalizada exitosamente"
            )
            
            return result
            
        except TransactionRejectedException:
            raise
        except Exception as e:
            logger.with_contexts(token=token).error(
                f"Error finalizando inscripción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def delete_inscription(self, tbk_user: str, username: str) -> Dict[str, Any]:
        """Delete card inscription"""
        try:
            logger.with_contexts(username=username, tbk_user=tbk_user[:10] + "...").info(
                "Eliminando inscripción"
            )
            
            response = self.mall_inscription.delete(tbk_user, username)
            
            logger.with_contexts(username=username, tbk_user=tbk_user[:10] + "...").info(
                "Inscripción eliminada exitosamente"
            )
            
            return {"deleted": True}
            
        except Exception as e:
            logger.with_contexts(username=username).error(
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
            logger.with_contexts(
                username=username,
                parent_buy_order=parent_buy_order,
                tbk_user=tbk_user[:10] + "...",
                details_count=len(details)
            ).info(
                "Autorizando transacción mall"
            )
            
            # Create transaction details
            # TODO: Revisar esta parte como realizar los cobros
            transaction_details = MallTransactionAuthorizeDetails(
                commerce_code=details[0]["commerce_code"],
                buy_order=details[0]["buy_order"],
                installments_number=details[0]["installments_number"],
                amount=details[0]["amount"]
            )
            for detail in details:
                transaction_details.add(
                    commerce_code=detail["commerce_code"],
                    buy_order=detail["buy_order"],
                    installments_number=detail["installments_number"],
                    amount=detail["amount"]
                )
            
            response = self.mall_transaction.authorize(
                username=username,
                tbk_user=tbk_user,
                parent_buy_order=parent_buy_order,
                details=transaction_details
            )
            
            # Process response details
            result_details = []
            for detail in response["details"]:
                if detail["response_code"] != 0:
                    logger.with_contexts(
                        username=username,
                        commerce_code=detail["commerce_code"],
                        response_code=detail["response_code"],
                        buy_order=detail["buy_order"],
                        amount=detail["amount"]
                    ).warning(
                        f"Transacción rechazada para comercio {detail['commerce_code']}"
                    )
                
                result_details.append({
                    "amount": detail["amount"],
                    "status": "approved" if detail["response_code"] == 0 else "rejected",
                    "authorization_code": detail["authorization_code"],
                    "payment_type_code": detail["payment_type_code"],
                    "response_code": detail["response_code"],
                    "installments_number": detail["installments_number"],
                    "commerce_code": detail["commerce_code"],
                    "buy_order": detail["buy_order"]
                })
            
            result = {
                "parent_buy_order": response["parent_buy_order"],
                "session_id": response["session_id"],
                "card_detail": {
                    "card_number": response["card_detail"]["card_number"]
                },
                "accounting_date": response["accounting_date"],
                "transaction_date": response["transaction_date"].isoformat(),
                "details": result_details
            }
            
            logger.with_contexts(
                username=username,
                parent_buy_order=parent_buy_order,
                session_id=response["session_id"],
                approved_count=len([d for d in result_details if d["status"] == "approved"])
            ).info(
                "Transacción autorizada exitosamente"
            )
            
            return result
            
        except Exception as e:
            logger.with_contexts(username=username).error(
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
            logger.with_contexts(child_buy_order=child_buy_order, child_commerce_code=child_commerce_code).info(
                "Consultando estado de transacción"
            )
            
            response = self.mall_transaction.status(
                buy_order=child_buy_order
            )
            
            result = {
                "buy_order": response["buy_order"],
                "session_id": response["session_id"],
                "card_detail": {
                    "card_number": response["card_detail"]["card_number"]
                },
                "accounting_date": response["accounting_date"],
                "transaction_date": response["transaction_date"].isoformat(),
                "details": [{
                    "amount": detail["amount"],
                    "status": "approved" if detail["response_code"] == 0 else "rejected",
                    "authorization_code": detail["authorization_code"],
                    "payment_type_code": detail["payment_type_code"],
                    "response_code": detail["response_code"],
                    "installments_number": detail["installments_number"],
                    "commerce_code": detail["commerce_code"],
                    "buy_order": detail["buy_order"],
                    "balance": detail.get("balance")
                } for detail in response["details"]]
            }
            
            logger.with_contexts(child_buy_order=child_buy_order).info(
                "Estado de transacción obtenido exitosamente"
            )
            
            return result
            
        except Exception as e:
            logger.with_contexts(child_buy_order=child_buy_order, child_commerce_code=child_commerce_code).error(
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
            logger.with_contexts(child_commerce_code=child_commerce_code, child_buy_order=child_buy_order, authorization_code=authorization_code, capture_amount=capture_amount).info(
                "Capturando transacción diferida"
            )
            
            response = self.mall_transaction.capture(
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                authorization_code=authorization_code,
                capture_amount=capture_amount
            )
            
            result = {
                "authorization_code": response["authorization_code"],
                "authorization_date": response["authorization_date"].isoformat(),
                "captured_amount": response["captured_amount"],
                "response_code": response["response_code"]
            }
            
            logger.with_contexts(child_buy_order=child_buy_order, captured_amount=capture_amount).info(
                "Transacción capturada exitosamente"
            )
            
            return result
            
        except Exception as e:
            logger.with_contexts(child_buy_order=child_buy_order, capture_amount=capture_amount).error(
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
            logger.with_contexts(child_commerce_code=child_commerce_code, child_buy_order=child_buy_order, amount=amount).info(
                "Reversando transacción"
            )
            
            response = self.mall_transaction.refund(
                child_commerce_code=child_commerce_code,
                child_buy_order=child_buy_order,
                amount=amount,
                buy_order=child_buy_order
            )
            
            result = {
                "type": response["type"],
                "response_code": response["response_code"],
                "reversed_amount": getattr(response, 'reversed_amount', amount)
            }
            
            logger.with_contexts(child_buy_order=child_buy_order, reversed_amount=amount).info(
                "Transacción reversada exitosamente"
            )
            
            return result
            
        except Exception as e:
            logger.with_contexts(child_buy_order=child_buy_order, amount=amount).error(
                f"Error reversando transacción: {str(e)}",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))