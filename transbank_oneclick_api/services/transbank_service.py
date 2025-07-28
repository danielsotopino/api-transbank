from typing import List, Dict, Any
import structlog
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction, MallTransactionAuthorizeDetails

from ..config import settings
from ..core.exceptions import (
    TransbankCommunicationException,
    TransactionRejectedException
)

logger = structlog.get_logger(__name__)

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
            logger.info(
                "Iniciando proceso de inscripción",
                context={
                    "username": username,
                    "email": email,
                    "response_url": response_url
                }
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
            
            logger.info(
                "Inscripción iniciada exitosamente",
                context={
                    "username": username,
                    "token": response["token"][:10] + "..."
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error iniciando inscripción: {str(e)}",
                context={
                    "username": username
                },
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def finish_inscription(self, token: str) -> Dict[str, Any]:
        """Finish card inscription process"""
        try:
            logger.info(
                "Finalizando proceso de inscripción",
                context={
                    "token": token[:10] + "..."
                }
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
            
            logger.info(
                "Inscripción finalizada exitosamente",
                context={
                    "tbk_user": response["tbk_user"][:10] + "...",
                    "card_type": response["card_type"],
                    "card_number": response["card_number"]
                }
            )
            
            return result
            
        except TransactionRejectedException:
            raise
        except Exception as e:
            logger.error(
                f"Error finalizando inscripción: {str(e)}",
                context={
                    "token": token
                },
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def delete_inscription(self, tbk_user: str, username: str) -> Dict[str, Any]:
        """Delete card inscription"""
        try:
            logger.info(
                "Eliminando inscripción",
                context={
                    "username": username,
                    "tbk_user": tbk_user[:10] + "..."
                }
            )
            
            response = self.mall_inscription.delete(tbk_user, username)
            
            logger.info(
                "Inscripción eliminada exitosamente",
                context={
                    "username": username,
                    "tbk_user": tbk_user[:10] + "..."
                }
            )
            
            return {"deleted": True}
            
        except Exception as e:
            logger.error(
                f"Error eliminando inscripción: {str(e)}",
                context={
                    "username": username
                },
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))
    
    async def authorize_transaction(
        self,
        username: str,
        tbk_user: str,
        buy_order: str,
        details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Authorize mall transaction"""
        try:
            logger.info(
                "Autorizando transacción mall",
                context={
                    "username": username,
                    "buy_order": buy_order,
                    "tbk_user": tbk_user[:10] + "...",
                    "details_count": len(details)
                }
            )
            
            # Create transaction details
            transaction_details = MallTransactionAuthorizeDetails(
                commerce_code=details[0]["commerce_code"],
                buy_order=buy_order,
                installments_number=0,
                amount=details[0]["amount"]
            )
            
            response = self.mall_transaction.authorize(
                username=username,
                tbk_user=tbk_user,
                parent_buy_order=buy_order,
                details=transaction_details
            )
            
            # Process response details
            print('response', response)

            result_details = []
            for detail in response["details"]:
                if detail["response_code"] != 0:
                    logger.warning(
                        f"Transacción rechazada para comercio {detail['commerce_code']}",
                        context={
                            "username": username,
                            "commerce_code": detail["commerce_code"],
                            "response_code": detail["response_code"],
                            "buy_order": detail["buy_order"],
                            "amount": detail["amount"]
                        }
                    )
                
                # payment_type_code values:
                # VD = Venta Débito
                # VP = Venta prepago
                # VN = Venta Normal
                # VC = Venta en cuotas
                # SI = 3 cuotas sin interés
                # S2 = 2 cuotas sin interés
                # NC = N Cuotas sin interés
                #
                # response_code values:
                # 0 = Transacción aprobada
                # Oneclick specific codes:
                # -96 = tbk_user no existente
                # -97 = Límites Oneclick, máximo monto diario de pago excedido
                # -98 = Límites Oneclick, máximo monto de pago excedido
                # -99 = Límites Oneclick, máxima cantidad de pagos diarios excedido
                result_details.append({
                    "amount": detail["amount"],
                    "status": "AUTHORIZED" if detail["response_code"] == 0 else "REJECTED",
                    "authorization_code": detail["authorization_code"],
                    "payment_type_code": detail["payment_type_code"],
                    "response_code": detail["response_code"],
                    "installments_number": detail["installments_number"],
                    "commerce_code": detail["commerce_code"],
                    "buy_order": detail["buy_order"]
                })
            
            result = {
                "buy_order": response["buy_order"],
                "card_detail": {
                    "card_number": response["card_detail"]["card_number"]
                },
                "accounting_date": response["accounting_date"],
                "transaction_date": response["transaction_date"],
                "details": result_details
            }
            
            logger.info(
                "Transacción autorizada exitosamente",
                context={
                    "username": username,
                    "buy_order": buy_order,
                    "approved_count": len([d for d in result_details if d["status"] == "AUTHORIZED"])
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error autorizando transacción: {str(e)}",
                context={
                    "username": username
                },
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
                context={
                    "child_buy_order": child_buy_order,
                    "child_commerce_code": child_commerce_code
                }
            )
            
            response = self.mall_transaction.status(
                buy_order=child_buy_order
            )
            
            result = {
                "buy_order": response["buy_order"],
                "card_detail": {
                    "card_number": response["card_detail"]["card_number"]
                },
                "accounting_date": response["accounting_date"],
                "transaction_date": response["transaction_date"].isoformat(),
                "details": [{
                    "amount": detail["amount"],
                    "status": "AUTHORIZED" if detail["response_code"] == 0 else "rejected",
                    "authorization_code": detail["authorization_code"],
                    "payment_type_code": detail["payment_type_code"],
                    "response_code": detail["response_code"],
                    "installments_number": detail["installments_number"],
                    "commerce_code": detail["commerce_code"],
                    "buy_order": detail["buy_order"],
                    "balance": detail.get("balance")
                } for detail in response["details"]]
            }
            
            logger.info(
                "Estado de transacción obtenido exitosamente",
                context={
                    "child_buy_order": child_buy_order
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error consultando estado de transacción: {str(e)}",
                context={
                    "child_buy_order": child_buy_order,
                    "child_commerce_code": child_commerce_code
                },
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
                context={
                    "child_commerce_code": child_commerce_code,
                    "child_buy_order": child_buy_order,
                    "authorization_code": authorization_code,
                    "capture_amount": capture_amount
                }
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
            
            logger.info(
                "Transacción capturada exitosamente",
                context={
                    "child_buy_order": child_buy_order,
                    "captured_amount": capture_amount
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error capturando transacción: {str(e)}",
                context={
                    "child_buy_order": child_buy_order,
                    "capture_amount": capture_amount
                },
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
                context={
                    "child_commerce_code": child_commerce_code,
                    "child_buy_order": child_buy_order,
                    "amount": amount
                }
                
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
            
            logger.info(
                "Transacción reversada exitosamente",
                context={
                    "child_buy_order": child_buy_order,
                    "reversed_amount": amount
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error reversando transacción: {str(e)}",
                context={
                    "child_buy_order": child_buy_order,
                    "amount": amount
                },
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise TransbankCommunicationException(str(e))