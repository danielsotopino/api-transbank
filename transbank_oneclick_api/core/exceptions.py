class DomainException(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ClientNotFoundedException(DomainException):
    def __init__(self, client_id: int):
        super().__init__(
            f"Cliente con ID {client_id} no encontrado",
            "CLIENT_NOT_FOUND"
        )


class UserNotFoundedException(DomainException):
    def __init__(self, username: str):
        super().__init__(
            f"Usuario {username} no encontrado",
            "USER_NOT_FOUND"
        )


class InscriptionNotFoundException(DomainException):
    def __init__(self, tbk_user: str):
        super().__init__(
            f"Inscripción no encontrada",
            "INSCRIPTION_NOT_FOUND"
        )


class TransactionRejectedException(DomainException):
    def __init__(self, response_code: int, message: str = None):
        default_message = f"Transacción rechazada con código {response_code}"
        super().__init__(
            message or default_message,
            "TRANSACTION_REJECTED"
        )


class TokenExpiradoException(DomainException):
    def __init__(self):
        super().__init__(
            "Token de inscripción expirado",
            "TOKEN_EXPIRADO"
        )


class OrdenCompraDuplicadaException(DomainException):
    def __init__(self, buy_order: str):
        super().__init__(
            f"Orden de compra {buy_order} ya existe",
            "ORDEN_COMPRA_DUPLICADA"
        )


class InvalidAmountException(DomainException):
    def __init__(self, amount: int):
        super().__init__(
            f"Monto {amount} es inválido",
            "INVALID_AMOUNT"
        )


class TransbankCommunicationException(DomainException):
    def __init__(self, original_error: str):
        super().__init__(
            f"Error de comunicación con Transbank: {original_error}",
            "TRANSBANK_COMMUNICATION_ERROR"
        )