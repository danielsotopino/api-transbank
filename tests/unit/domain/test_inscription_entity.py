import pytest
from datetime import datetime
from transbank_oneclick_api.domain.entities.inscription import (
    InscriptionEntity,
    InscriptionStatus,
    CardDetails
)


class TestCardDetails:
    """Tests for CardDetails value object."""

    def test_create_valid_card_details(self):
        """Test creating valid card details."""
        card_details = CardDetails(
            card_type="Visa",
            card_number="****1234"
        )

        assert card_details.card_type == "Visa"
        assert card_details.card_number == "****1234"

    def test_card_number_too_short_raises_error(self):
        """Test that card number with less than 4 characters raises error."""
        with pytest.raises(ValueError, match="Invalid card number format"):
            CardDetails(card_type="Visa", card_number="123")

    def test_empty_card_number_raises_error(self):
        """Test that empty card number raises error."""
        with pytest.raises(ValueError, match="Invalid card number format"):
            CardDetails(card_type="Visa", card_number="")

    def test_empty_card_type_raises_error(self):
        """Test that empty card type raises error."""
        with pytest.raises(ValueError, match="Card type is required"):
            CardDetails(card_type="", card_number="****1234")

    def test_is_masked_returns_true_for_masked_number(self):
        """Test is_masked returns True for properly masked numbers."""
        card_details = CardDetails(
            card_type="Visa",
            card_number="****1234"
        )
        assert card_details.is_masked() is True

    def test_is_masked_returns_false_for_unmasked_number(self):
        """Test is_masked returns False for unmasked numbers."""
        card_details = CardDetails(
            card_type="Visa",
            card_number="12341234"
        )
        assert card_details.is_masked() is False


class TestInscriptionEntity:
    """Tests for InscriptionEntity domain entity."""

    def test_create_valid_inscription_entity(self):
        """Test creating valid inscription entity."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        assert inscription.username == "testuser"
        assert inscription.email == "test@example.com"
        assert inscription.tbk_user == "tbk_test_123"
        assert inscription.url_webpay == "https://webpay.test.com"
        assert inscription.status == InscriptionStatus.PENDING
        assert inscription.id is None
        assert inscription.card_details is None

    def test_username_too_short_raises_error(self):
        """Test that username with less than 3 characters raises error."""
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            InscriptionEntity(
                username="ab",
                email="test@example.com",
                tbk_user="tbk_test",
                url_webpay="https://test.com",
                status=InscriptionStatus.PENDING
            )

    def test_invalid_email_raises_error(self):
        """Test that invalid email format raises error."""
        with pytest.raises(ValueError, match="Invalid email format"):
            InscriptionEntity(
                username="testuser",
                email="invalid_email",
                tbk_user="tbk_test",
                url_webpay="https://test.com",
                status=InscriptionStatus.PENDING
            )

    def test_empty_tbk_user_raises_error(self):
        """Test that empty tbk_user raises error."""
        with pytest.raises(ValueError, match="Transbank user token is required"):
            InscriptionEntity(
                username="testuser",
                email="test@example.com",
                tbk_user="",
                url_webpay="https://test.com",
                status=InscriptionStatus.PENDING
            )

    def test_empty_url_webpay_raises_error(self):
        """Test that empty url_webpay raises error."""
        with pytest.raises(ValueError, match="Webpay URL is required"):
            InscriptionEntity(
                username="testuser",
                email="test@example.com",
                tbk_user="tbk_test",
                url_webpay="",
                status=InscriptionStatus.PENDING
            )

    def test_complete_inscription_success(self):
        """Test completing inscription successfully."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        card_details = CardDetails(
            card_type="Visa",
            card_number="****1234"
        )

        inscription.complete_inscription("auth_code_123", card_details)

        assert inscription.status == InscriptionStatus.COMPLETED
        assert inscription.authorization_code == "auth_code_123"
        assert inscription.card_details == card_details
        assert inscription.updated_at is not None

    def test_complete_inscription_already_completed_raises_error(self):
        """Test that completing already completed inscription raises error."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.COMPLETED
        )

        card_details = CardDetails(
            card_type="Visa",
            card_number="****1234"
        )

        with pytest.raises(ValueError, match="Cannot complete inscription"):
            inscription.complete_inscription("auth_code", card_details)

    def test_complete_inscription_without_auth_code_raises_error(self):
        """Test that completing without authorization code raises error."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        card_details = CardDetails(
            card_type="Visa",
            card_number="****1234"
        )

        with pytest.raises(ValueError, match="Authorization code is required"):
            inscription.complete_inscription("", card_details)

    def test_is_active_returns_true_for_completed(self):
        """Test is_active returns True for completed inscriptions."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.COMPLETED
        )

        assert inscription.is_active() is True

    def test_is_active_returns_false_for_pending(self):
        """Test is_active returns False for pending inscriptions."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        assert inscription.is_active() is False

    def test_expire_success(self):
        """Test expiring pending inscription."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        inscription.expire()

        assert inscription.status == InscriptionStatus.EXPIRED
        assert inscription.updated_at is not None

    def test_expire_non_pending_raises_error(self):
        """Test that expiring non-pending inscription raises error."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.COMPLETED
        )

        with pytest.raises(ValueError, match="Cannot expire inscription"):
            inscription.expire()

    def test_fail_inscription(self):
        """Test failing inscription."""
        inscription = InscriptionEntity(
            username="testuser",
            email="test@example.com",
            tbk_user="tbk_test_123",
            url_webpay="https://webpay.test.com",
            status=InscriptionStatus.PENDING
        )

        inscription.fail("Test reason")

        assert inscription.status == InscriptionStatus.FAILED
        assert inscription.updated_at is not None
