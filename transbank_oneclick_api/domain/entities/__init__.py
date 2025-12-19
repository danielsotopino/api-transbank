"""Domain entities for Transbank Oneclick API."""
from .inscription import InscriptionEntity, InscriptionStatus, CardDetails
from .transaction import (
    TransactionEntity,
    TransactionDetail,
    TransactionStatus,
    PaymentType,
    Amount
)

__all__ = [
    "InscriptionEntity",
    "InscriptionStatus",
    "CardDetails",
    "TransactionEntity",
    "TransactionDetail",
    "TransactionStatus",
    "PaymentType",
    "Amount",
]
