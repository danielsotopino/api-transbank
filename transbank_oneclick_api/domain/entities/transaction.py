from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
from decimal import Decimal


class TransactionStatus(str, Enum):
    """Status values for transaction."""
    AUTHORIZED = "AUTHORIZED"
    REVERSED = "REVERSED"
    FAILED = "FAILED"
    CAPTURED = "CAPTURED"


class PaymentType(str, Enum):
    """Payment type codes from Transbank."""
    VENTA_DEBITO = "VD"
    VENTA_CREDITO = "VN"
    VENTA_3_CUOTAS = "VC"
    VENTA_CUOTAS = "VN"
    VENTA_PREPAGO = "VP"
    VENTA_SIN_CVV = "S2"
    VENTA_SIN_CVV_CUOTAS = "SI"


@dataclass
class Amount:
    """Value Object for monetary amounts."""
    value: int  # Amount in smallest currency unit (e.g., cents)

    def __post_init__(self):
        """Validate amount."""
        if self.value < 0:
            raise ValueError("Amount cannot be negative")
        if self.value == 0:
            raise ValueError("Amount must be greater than zero")

    def to_decimal(self) -> Decimal:
        """Convert to decimal representation."""
        return Decimal(self.value) / Decimal(100)

    def __str__(self) -> str:
        return f"${self.to_decimal():.2f}"


@dataclass
class TransactionDetail:
    """Domain Entity for transaction detail (per commerce)."""
    commerce_code: str
    buy_order: str
    amount: Amount
    status: TransactionStatus
    authorization_code: Optional[str] = None
    payment_type_code: Optional[PaymentType] = None
    response_code: Optional[int] = None
    installments_number: Optional[int] = None
    id: Optional[str] = None

    def __post_init__(self):
        """Validate detail."""
        if not self.commerce_code:
            raise ValueError("Commerce code is required")
        if not self.buy_order:
            raise ValueError("Buy order is required")
        if len(self.buy_order) > 26:
            raise ValueError("Buy order must be max 26 characters")

    def is_authorized(self) -> bool:
        """Check if detail was authorized successfully."""
        return (
            self.status == TransactionStatus.AUTHORIZED and
            self.response_code == 0 and
            self.authorization_code is not None
        )

    def is_reversible(self) -> bool:
        """Check if detail can be reversed."""
        return self.status == TransactionStatus.AUTHORIZED


@dataclass
class TransactionEntity:
    """
    Domain Entity for Oneclick Mall Transaction.

    Aggregates multiple transaction details (one per commerce).
    """
    username: str
    buy_order: str
    details: List[TransactionDetail] = field(default_factory=list)
    id: Optional[str] = None
    inscription_id: Optional[str] = None
    card_number: Optional[str] = None
    accounting_date: Optional[str] = None
    transaction_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity."""
        self._validate()

    def _validate(self):
        """Business validation rules."""
        if not self.username:
            raise ValueError("Username is required")

        if not self.buy_order:
            raise ValueError("Buy order is required")

        if len(self.buy_order) > 26:
            raise ValueError("Buy order must be max 26 characters")

        if self.details and len(self.details) == 0:
            raise ValueError("Transaction must have at least one detail")

    def add_detail(self, detail: TransactionDetail) -> None:
        """Add a transaction detail."""
        if detail in self.details:
            raise ValueError("Detail already exists in transaction")

        self.details.append(detail)

    def get_total_amount(self) -> Amount:
        """Calculate total amount across all details."""
        total = sum(detail.amount.value for detail in self.details)
        return Amount(value=total)

    def is_fully_authorized(self) -> bool:
        """Check if all details were authorized."""
        if not self.details:
            return False
        return all(detail.is_authorized() for detail in self.details)

    def has_failed_details(self) -> bool:
        """Check if any detail failed."""
        return any(
            detail.status == TransactionStatus.FAILED
            for detail in self.details
        )

    def get_authorized_details(self) -> List[TransactionDetail]:
        """Get only authorized details."""
        return [
            detail for detail in self.details
            if detail.is_authorized()
        ]

    def can_be_refunded(self) -> bool:
        """Check if transaction can be refunded."""
        return self.is_fully_authorized()
