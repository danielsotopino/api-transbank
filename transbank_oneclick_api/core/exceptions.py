from transbank_oneclick_api.core.response_codes import ResponseCode


class DomainException(Exception):
    """
    Base exception for domain errors.

    Usage:
        raise DomainException(ResponseCodes.INSCRIPTION_NOT_FOUND)
        raise DomainException(
            ResponseCodes.TRANSACTION_REJECTED,
            custom_message="Card declined by issuer"
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


class ClientNotFoundedException(DomainException):
    """Exception for client not found."""
    def __init__(self, client_id: int):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.CLIENT_NOT_FOUND,
            custom_message=f"Cliente con ID {client_id} no encontrado"
        )


class UserNotFoundedException(DomainException):
    """Exception for user not found."""
    def __init__(self, username: str):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.NOT_FOUND,
            custom_message=f"Usuario {username} no encontrado"
        )


class InscriptionNotFoundException(DomainException):
    """Exception for inscription not found."""
    def __init__(self, username: str):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.INSCRIPTION_NOT_FOUND,
            custom_message=f"Inscription not found for user: {username}"
        )


class TransactionRejectedException(DomainException):
    """Exception for rejected transactions."""
    def __init__(self, response_code: int, message: str = None):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        default_message = f"Transacción rechazada con código {response_code}"
        super().__init__(
            ResponseCodes.TRANSACTION_REJECTED,
            custom_message=message or default_message,
            details={"transbank_response_code": response_code}
        )


class TokenExpiradoException(DomainException):
    """Exception for expired inscription token."""
    def __init__(self):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.INSCRIPTION_EXPIRED,
            custom_message="Token de inscripción expirado"
        )


class OrdenCompraDuplicadaException(DomainException):
    """Exception for duplicate buy order."""
    def __init__(self, buy_order: str):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.ORDEN_COMPRA_DUPLICADA,
            custom_message=f"Orden de compra {buy_order} ya existe",
            details={"buy_order": buy_order}
        )


class InvalidAmountException(DomainException):
    """Exception for invalid transaction amount."""
    def __init__(self, amount: int):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.INVALID_AMOUNT,
            custom_message=f"Monto {amount} es inválido",
            details={"amount": amount}
        )


class TransbankCommunicationException(DomainException):
    """Exception for Transbank communication errors."""
    def __init__(self, original_error: str):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(
            ResponseCodes.TRANSBANK_COMMUNICATION_ERROR,
            custom_message=f"Error de comunicación con Transbank: {original_error}",
            details={"original_error": original_error}
        )


class InsufficientBalanceException(DomainException):
    """Exception for insufficient balance."""
    def __init__(self):
        from transbank_oneclick_api.core.response_codes import ResponseCodes
        super().__init__(ResponseCodes.INSUFFICIENT_BALANCE)