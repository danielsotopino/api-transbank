import pytest
from datetime import datetime
from decimal import Decimal
from transbank_oneclick_api.domain.entities.transaction import (
    TransactionEntity,
    TransactionDetail,
    TransactionStatus,
    PaymentType,
    Amount
)


class TestAmount:
    """Tests for Amount value object."""

    def test_create_valid_amount(self):
        """Test creating valid amount."""
        amount = Amount(value=1000)
        assert amount.value == 1000

    def test_negative_amount_raises_error(self):
        """Test that negative amount raises error."""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            Amount(value=-100)

    def test_zero_amount_raises_error(self):
        """Test that zero amount raises error."""
        with pytest.raises(ValueError, match="Amount must be greater than zero"):
            Amount(value=0)

    def test_to_decimal_conversion(self):
        """Test converting to decimal."""
        amount = Amount(value=1500)
        assert amount.to_decimal() == Decimal("15.00")

    def test_str_representation(self):
        """Test string representation."""
        amount = Amount(value=2500)
        assert str(amount) == "$25.00"


class TestTransactionDetail:
    """Tests for TransactionDetail entity."""

    def test_create_valid_transaction_detail(self):
        """Test creating valid transaction detail."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            payment_type_code=PaymentType.VENTA_CREDITO,
            response_code=0,
            installments_number=1
        )

        assert detail.commerce_code == "597055555532"
        assert detail.buy_order == "detail_001"
        assert detail.amount.value == 1000
        assert detail.status == TransactionStatus.AUTHORIZED
        assert detail.authorization_code == "1213"
        assert detail.payment_type_code == PaymentType.VENTA_CREDITO
        assert detail.response_code == 0

    def test_empty_commerce_code_raises_error(self):
        """Test that empty commerce code raises error."""
        with pytest.raises(ValueError, match="Commerce code is required"):
            TransactionDetail(
                commerce_code="",
                buy_order="detail_001",
                amount=Amount(value=1000),
                status=TransactionStatus.AUTHORIZED
            )

    def test_empty_buy_order_raises_error(self):
        """Test that empty buy order raises error."""
        with pytest.raises(ValueError, match="Buy order is required"):
            TransactionDetail(
                commerce_code="597055555532",
                buy_order="",
                amount=Amount(value=1000),
                status=TransactionStatus.AUTHORIZED
            )

    def test_buy_order_too_long_raises_error(self):
        """Test that buy order longer than 26 chars raises error."""
        with pytest.raises(ValueError, match="Buy order must be max 26 characters"):
            TransactionDetail(
                commerce_code="597055555532",
                buy_order="a" * 27,
                amount=Amount(value=1000),
                status=TransactionStatus.AUTHORIZED
            )

    def test_is_authorized_returns_true_for_successful(self):
        """Test is_authorized returns True for successful authorization."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        assert detail.is_authorized() is True

    def test_is_authorized_returns_false_for_failed(self):
        """Test is_authorized returns False for failed authorization."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.FAILED,
            response_code=1
        )

        assert detail.is_authorized() is False

    def test_is_authorized_returns_false_without_auth_code(self):
        """Test is_authorized returns False without auth code."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            response_code=0
        )

        assert detail.is_authorized() is False

    def test_is_reversible_returns_true_for_authorized(self):
        """Test is_reversible returns True for authorized transactions."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED
        )

        assert detail.is_reversible() is True

    def test_is_reversible_returns_false_for_reversed(self):
        """Test is_reversible returns False for reversed transactions."""
        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.REVERSED
        )

        assert detail.is_reversible() is False


class TestTransactionEntity:
    """Tests for TransactionEntity domain entity."""

    def test_create_valid_transaction_entity(self):
        """Test creating valid transaction entity."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        assert transaction.username == "testuser"
        assert transaction.buy_order == "buy_order_123"
        assert transaction.details == []

    def test_empty_username_raises_error(self):
        """Test that empty username raises error."""
        with pytest.raises(ValueError, match="Username is required"):
            TransactionEntity(
                username="",
                buy_order="buy_order_123"
            )

    def test_empty_buy_order_raises_error(self):
        """Test that empty buy order raises error."""
        with pytest.raises(ValueError, match="Buy order is required"):
            TransactionEntity(
                username="testuser",
                buy_order=""
            )

    def test_buy_order_too_long_raises_error(self):
        """Test that buy order longer than 26 chars raises error."""
        with pytest.raises(ValueError, match="Buy order must be max 26 characters"):
            TransactionEntity(
                username="testuser",
                buy_order="a" * 27
            )

    def test_add_detail_success(self):
        """Test adding detail to transaction."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED
        )

        transaction.add_detail(detail)

        assert len(transaction.details) == 1
        assert transaction.details[0] == detail

    def test_add_duplicate_detail_raises_error(self):
        """Test that adding duplicate detail raises error."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED
        )

        transaction.add_detail(detail)

        with pytest.raises(ValueError, match="Detail already exists"):
            transaction.add_detail(detail)

    def test_get_total_amount(self):
        """Test calculating total amount."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail1 = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED
        )

        detail2 = TransactionDetail(
            commerce_code="597055555533",
            buy_order="detail_002",
            amount=Amount(value=2000),
            status=TransactionStatus.AUTHORIZED
        )

        transaction.add_detail(detail1)
        transaction.add_detail(detail2)

        total = transaction.get_total_amount()
        assert total.value == 3000

    def test_is_fully_authorized_returns_true_all_authorized(self):
        """Test is_fully_authorized returns True when all details authorized."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail1 = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        detail2 = TransactionDetail(
            commerce_code="597055555533",
            buy_order="detail_002",
            amount=Amount(value=2000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1214",
            response_code=0
        )

        transaction.add_detail(detail1)
        transaction.add_detail(detail2)

        assert transaction.is_fully_authorized() is True

    def test_is_fully_authorized_returns_false_if_any_failed(self):
        """Test is_fully_authorized returns False if any detail failed."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail1 = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        detail2 = TransactionDetail(
            commerce_code="597055555533",
            buy_order="detail_002",
            amount=Amount(value=2000),
            status=TransactionStatus.FAILED,
            response_code=1
        )

        transaction.add_detail(detail1)
        transaction.add_detail(detail2)

        assert transaction.is_fully_authorized() is False

    def test_has_failed_details_returns_true(self):
        """Test has_failed_details returns True when there are failures."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.FAILED
        )

        transaction.add_detail(detail)

        assert transaction.has_failed_details() is True

    def test_has_failed_details_returns_false(self):
        """Test has_failed_details returns False when no failures."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        transaction.add_detail(detail)

        assert transaction.has_failed_details() is False

    def test_get_authorized_details(self):
        """Test getting only authorized details."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail1 = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        detail2 = TransactionDetail(
            commerce_code="597055555533",
            buy_order="detail_002",
            amount=Amount(value=2000),
            status=TransactionStatus.FAILED,
            response_code=1
        )

        transaction.add_detail(detail1)
        transaction.add_detail(detail2)

        authorized = transaction.get_authorized_details()

        assert len(authorized) == 1
        assert authorized[0] == detail1

    def test_can_be_refunded(self):
        """Test can_be_refunded returns True when fully authorized."""
        transaction = TransactionEntity(
            username="testuser",
            buy_order="buy_order_123"
        )

        detail = TransactionDetail(
            commerce_code="597055555532",
            buy_order="detail_001",
            amount=Amount(value=1000),
            status=TransactionStatus.AUTHORIZED,
            authorization_code="1213",
            response_code=0
        )

        transaction.add_detail(detail)

        assert transaction.can_be_refunded() is True
