from typing import NamedTuple


class ResponseCode(NamedTuple):
    """
    Response code structure with code, message, and HTTP status.

    Attributes:
        code: Unique identifier for the response
        message: Default human-readable message
        http_status: HTTP status code to return
    """
    code: str
    message: str
    http_status: int = 200


class ResponseCodes:
    """
    Centralized response code registry for Transbank Oneclick API.

    Format for domain codes: <DOMAIN>_<NUMBER>
    - DOMAIN: 3-letter code identifying the domain (TBK, INS, TXN)
    - NUMBER: Sequential 3-digit number (001, 002, etc.)

    Usage:
        raise ServiceException(ResponseCodes.INSCRIPTION_NOT_FOUND)
        raise TransbankException(ResponseCodes.TRANSBANK_TIMEOUT)
    """

    # ==================== STANDARD CODES ====================
    SUCCESS = ResponseCode("00", "Operation successful", 200)
    BAD_REQUEST = ResponseCode("01", "Invalid request data", 400)
    UNAUTHORIZED = ResponseCode("401", "Authentication required", 401)
    FORBIDDEN = ResponseCode("403", "Access denied", 403)
    NOT_FOUND = ResponseCode("404", "Resource not found", 404)
    CONFLICT = ResponseCode("409", "Resource conflict", 409)
    INTERNAL_ERROR = ResponseCode("500", "Internal server error", 500)

    # ==================== INSCRIPTION DOMAIN (INS) ====================
    INSCRIPTION_NOT_FOUND = ResponseCode(
        "INS_001",
        "Inscription not found",
        404
    )
    INSCRIPTION_ALREADY_EXISTS = ResponseCode(
        "INS_002",
        "User already has an active inscription",
        409
    )
    INSCRIPTION_INCOMPLETE = ResponseCode(
        "INS_003",
        "Inscription process not completed",
        400
    )
    INSCRIPTION_EXPIRED = ResponseCode(
        "INS_004",
        "Inscription has expired",
        400
    )
    INVALID_INSCRIPTION_STATUS = ResponseCode(
        "INS_005",
        "Invalid inscription status",
        400
    )

    # ==================== TRANSACTION DOMAIN (TXN) ====================
    TRANSACTION_NOT_FOUND = ResponseCode(
        "TXN_001",
        "Transaction not found",
        404
    )
    TRANSACTION_REJECTED = ResponseCode(
        "TXN_002",
        "Transaction rejected by Transbank",
        402
    )
    INSUFFICIENT_BALANCE = ResponseCode(
        "TXN_003",
        "Insufficient balance",
        402
    )
    INVALID_CARD = ResponseCode(
        "TXN_004",
        "Invalid card",
        400
    )
    TRANSACTION_ALREADY_PROCESSED = ResponseCode(
        "TXN_005",
        "Transaction already processed",
        409
    )
    INVALID_AMOUNT = ResponseCode(
        "TXN_006",
        "Invalid transaction amount",
        400
    )
    REFUND_FAILED = ResponseCode(
        "TXN_007",
        "Refund operation failed",
        500
    )
    ORDEN_COMPRA_DUPLICADA = ResponseCode(
        "TXN_008",
        "Duplicate buy order",
        409
    )

    # ==================== TRANSBANK DOMAIN (TBK) ====================
    TRANSBANK_TIMEOUT = ResponseCode(
        "TBK_001",
        "Transbank service timeout",
        504
    )
    TRANSBANK_COMMUNICATION_ERROR = ResponseCode(
        "TBK_002",
        "Error communicating with Transbank",
        502
    )
    TRANSBANK_INVALID_RESPONSE = ResponseCode(
        "TBK_003",
        "Invalid response from Transbank",
        502
    )
    TRANSBANK_AUTHENTICATION_ERROR = ResponseCode(
        "TBK_004",
        "Transbank authentication failed",
        401
    )
    TRANSBANK_SERVICE_UNAVAILABLE = ResponseCode(
        "TBK_005",
        "Transbank service unavailable",
        503
    )

    # ==================== CLIENT DOMAIN (CLI) ====================
    CLIENT_NOT_FOUND = ResponseCode(
        "CLI_001",
        "Client not found",
        404
    )
    INVALID_CLIENT_DATA = ResponseCode(
        "CLI_002",
        "Invalid client data",
        400
    )
