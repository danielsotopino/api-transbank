from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class InscriptionStatus(str, Enum):
    """Status values for inscription lifecycle."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


@dataclass
class CardDetails:
    """Value Object for card information."""
    card_type: str
    card_number: str  # Masked (e.g., "****1234")

    def __post_init__(self):
        """Validate card details."""
        if not self.card_number or len(self.card_number) < 4:
            raise ValueError("Invalid card number format")
        if not self.card_type:
            raise ValueError("Card type is required")

    def is_masked(self) -> bool:
        """Check if card number is properly masked."""
        return self.card_number.startswith("****")


@dataclass
class InscriptionEntity:
    """
    Domain Entity for Oneclick Inscription.

    Pure business object - no SQLAlchemy dependencies.
    Contains business logic and validations.
    """
    username: str
    email: str
    tbk_user: str
    url_webpay: str
    status: InscriptionStatus
    id: Optional[int] = None
    card_details: Optional[CardDetails] = None
    authorization_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity on creation."""
        self._validate()

    def _validate(self):
        """Business validation rules."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")

        if not self.tbk_user:
            raise ValueError("Transbank user token is required")

        if not self.url_webpay:
            raise ValueError("Webpay URL is required")

    def complete_inscription(
        self,
        authorization_code: str,
        card_details: CardDetails
    ) -> None:
        """
        Complete inscription process.

        Business Rule: Can only complete PENDING inscriptions.
        """
        if self.status != InscriptionStatus.PENDING:
            raise ValueError(
                f"Cannot complete inscription in {self.status} status"
            )

        if not authorization_code:
            raise ValueError("Authorization code is required")

        self.status = InscriptionStatus.COMPLETED
        self.authorization_code = authorization_code
        self.card_details = card_details
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if inscription is active and usable."""
        return self.status == InscriptionStatus.COMPLETED

    def expire(self) -> None:
        """
        Mark inscription as expired.

        Business Rule: Can only expire PENDING inscriptions.
        """
        if self.status != InscriptionStatus.PENDING:
            raise ValueError(
                f"Cannot expire inscription in {self.status} status"
            )

        self.status = InscriptionStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def fail(self, reason: str = None) -> None:
        """Mark inscription as failed."""
        self.status = InscriptionStatus.FAILED
        self.updated_at = datetime.utcnow()
