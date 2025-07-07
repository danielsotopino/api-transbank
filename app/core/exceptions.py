class DomainException(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ClienteNoEncontradoException(DomainException):
    def __init__(self, cliente_id: int):
        super().__init__(
            f"Cliente con ID {cliente_id} no encontrado",
            "CLIENTE_NO_ENCONTRADO"
        )


class UsuarioNoEncontradoException(DomainException):
    def __init__(self, username: str):
        super().__init__(
            f"Usuario {username} no encontrado",
            "USUARIO_NO_ENCONTRADO"
        )


class InscripcionNoEncontradaException(DomainException):
    def __init__(self, tbk_user: str):
        super().__init__(
            f"Inscripción no encontrada",
            "INSCRIPCION_NO_ENCONTRADA"
        )


class TransaccionRechazadaException(DomainException):
    def __init__(self, response_code: int, message: str = None):
        default_message = f"Transacción rechazada con código {response_code}"
        super().__init__(
            message or default_message,
            "TRANSACCION_RECHAZADA"
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


class MontoInvalidoException(DomainException):
    def __init__(self, monto: int):
        super().__init__(
            f"Monto {monto} es inválido",
            "MONTO_INVALIDO"
        )


class TransbankCommunicationException(DomainException):
    def __init__(self, original_error: str):
        super().__init__(
            f"Error de comunicación con Transbank: {original_error}",
            "TRANSBANK_COMMUNICATION_ERROR"
        )