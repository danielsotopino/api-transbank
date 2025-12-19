import pytest
from datetime import datetime

from transbank_oneclick_api.repositories.transaction_repository import TransactionRepository
from transbank_oneclick_api.models.oneclick_transaction import OneclickTransaction, OneclickTransactionDetail


class TestTransactionRepository:
    """Test suite for TransactionRepository"""

    def test_create_transaction(self, db_session):
        """Test creating a basic transaction"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_123",
            "username": "testuser",
            "buy_order": "buy_order_123",
            "card_number": "****1234",
            "accounting_date": "2025-01-01",
            "transaction_date": datetime.utcnow()
        }

        transaction = repo.create(transaction_data)
        db_session.commit()

        assert transaction.id == "buy_order_123"
        assert transaction.username == "testuser"
        assert transaction.buy_order == "buy_order_123"
        assert transaction.card_number == "****1234"

    def test_create_with_details(self, db_session):
        """Test creating transaction with details in a single operation"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_456",
            "username": "testuser2",
            "buy_order": "buy_order_456",
            "card_number": "****5678"
        }

        details_data = [
            {
                "buy_order": "detail_001",
                "commerce_code": "597055555532",
                "amount": 10000,
                "status": "AUTHORIZED",
                "authorization_code": "1213",
                "payment_type_code": "VN",
                "response_code": 0,
                "installments_number": 1
            },
            {
                "buy_order": "detail_002",
                "commerce_code": "597055555533",
                "amount": 25000,
                "status": "AUTHORIZED",
                "authorization_code": "1214",
                "payment_type_code": "VN",
                "response_code": 0,
                "installments_number": 3
            }
        ]

        transaction = repo.create_with_details(transaction_data, details_data)
        db_session.commit()

        assert transaction.id == "buy_order_456"
        assert len(transaction.details) == 2
        assert transaction.details[0].amount == 10000
        assert transaction.details[0].commerce_code == "597055555532"
        assert transaction.details[1].amount == 25000
        assert transaction.details[1].installments_number == 3

    def test_create_with_details_empty_list(self, db_session):
        """Test creating transaction with empty details list"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_empty",
            "username": "testuser3",
            "buy_order": "buy_order_empty"
        }

        transaction = repo.create_with_details(transaction_data, [])
        db_session.commit()

        assert transaction.id == "buy_order_empty"
        assert len(transaction.details) == 0

    def test_get_by_id(self, db_session):
        """Test retrieving transaction by ID"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_get",
            "username": "testuser4",
            "buy_order": "buy_order_get"
        }

        created = repo.create(transaction_data)
        db_session.commit()

        retrieved = repo.get_by_id("buy_order_get")

        assert retrieved is not None
        assert retrieved.id == "buy_order_get"
        assert retrieved.username == "testuser4"

    def test_get_by_id_not_found(self, db_session):
        """Test retrieving non-existent transaction returns None"""
        repo = TransactionRepository(db_session)

        transaction = repo.get_by_id("nonexistent_order")

        assert transaction is None

    def test_get_by_id_with_details(self, db_session):
        """Test retrieving transaction with details eagerly loaded"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_eager",
            "username": "testuser5",
            "buy_order": "buy_order_eager"
        }

        details_data = [
            {
                "buy_order": "detail_eager_1",
                "commerce_code": "597055555534",
                "amount": 15000,
                "status": "AUTHORIZED",
                "authorization_code": "1215",
                "payment_type_code": "VN",
                "response_code": 0,
                "installments_number": 1
            }
        ]

        created = repo.create_with_details(transaction_data, details_data)
        db_session.commit()

        transaction = repo.get_by_id_with_details(created.id)

        assert transaction is not None
        assert transaction.id == "buy_order_eager"
        assert len(transaction.details) == 1
        assert transaction.details[0].amount == 15000

    def test_get_by_username(self, db_session):
        """Test retrieving transactions by username"""
        repo = TransactionRepository(db_session)

        # Create multiple transactions for same user
        for i in range(3):
            transaction_data = {
                "id": f"buy_order_user_{i}",
                "username": "testuser_multi",
                "buy_order": f"buy_order_user_{i}"
            }
            repo.create(transaction_data)

        db_session.commit()

        transactions = repo.get_by_username("testuser_multi")

        assert len(transactions) >= 3
        assert all(t.username == "testuser_multi" for t in transactions)
        assert all(isinstance(t, OneclickTransaction) for t in transactions)

    def test_get_by_username_with_pagination(self, db_session):
        """Test retrieving transactions with pagination"""
        repo = TransactionRepository(db_session)

        # Create 10 transactions
        for i in range(10):
            transaction_data = {
                "id": f"buy_order_paginate_{i}",
                "username": "testuser_paginate",
                "buy_order": f"buy_order_paginate_{i}"
            }
            repo.create(transaction_data)

        db_session.commit()

        # Test pagination
        page1 = repo.get_by_username("testuser_paginate", skip=0, limit=5)
        assert len(page1) == 5

        page2 = repo.get_by_username("testuser_paginate", skip=5, limit=5)
        assert len(page2) == 5

        # Verify different transactions
        page1_ids = {t.id for t in page1}
        page2_ids = {t.id for t in page2}
        assert len(page1_ids & page2_ids) == 0  # No overlap

    def test_get_by_username_empty_result(self, db_session):
        """Test retrieving transactions for user with no transactions"""
        repo = TransactionRepository(db_session)

        transactions = repo.get_by_username("nonexistent_user")

        assert len(transactions) == 0
        assert transactions == []

    def test_get_by_buy_order(self, db_session):
        """Test retrieving transaction by buy_order"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "unique_buy_order_789",
            "username": "testuser6",
            "buy_order": "unique_buy_order_789",
            "card_number": "****9999"
        }

        repo.create(transaction_data)
        db_session.commit()

        transaction = repo.get_by_buy_order("unique_buy_order_789")

        assert transaction is not None
        assert transaction.buy_order == "unique_buy_order_789"
        assert transaction.username == "testuser6"
        assert transaction.card_number == "****9999"

    def test_get_by_buy_order_not_found(self, db_session):
        """Test retrieving non-existent buy_order returns None"""
        repo = TransactionRepository(db_session)

        transaction = repo.get_by_buy_order("nonexistent_buy_order")

        assert transaction is None

    def test_update_transaction(self, db_session):
        """Test updating a transaction"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_update",
            "username": "testuser7",
            "buy_order": "buy_order_update",
            "card_number": "****1111"
        }

        created = repo.create(transaction_data)
        db_session.commit()

        # Update transaction
        updated = repo.update("buy_order_update", {
            "card_number": "****2222",
            "accounting_date": "2025-01-15"
        })
        db_session.commit()

        assert updated is not None
        assert updated.card_number == "****2222"
        assert updated.accounting_date == "2025-01-15"

    def test_delete_transaction(self, db_session):
        """Test deleting a transaction"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_delete",
            "username": "testuser8",
            "buy_order": "buy_order_delete"
        }

        created = repo.create(transaction_data)
        db_session.commit()

        # Delete transaction
        result = repo.delete("buy_order_delete")
        db_session.commit()

        assert result is True

        # Verify deletion
        deleted = repo.get_by_id("buy_order_delete")
        assert deleted is None

    def test_delete_nonexistent_transaction(self, db_session):
        """Test deleting non-existent transaction returns False"""
        repo = TransactionRepository(db_session)

        result = repo.delete("nonexistent_transaction")

        assert result is False

    def test_transaction_detail_cascade(self, db_session):
        """Test that transaction details are properly associated"""
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": "buy_order_cascade",
            "username": "testuser9",
            "buy_order": "buy_order_cascade"
        }

        details_data = [
            {
                "buy_order": "detail_cascade_1",
                "commerce_code": "597055555535",
                "amount": 30000,
                "status": "AUTHORIZED",
                "authorization_code": "1216",
                "payment_type_code": "VN",
                "response_code": 0,
                "installments_number": 6
            },
            {
                "buy_order": "detail_cascade_2",
                "commerce_code": "597055555536",
                "amount": 40000,
                "status": "REJECTED",
                "authorization_code": None,
                "payment_type_code": "VN",
                "response_code": 1,
                "installments_number": 1
            }
        ]

        transaction = repo.create_with_details(transaction_data, details_data)
        db_session.commit()

        # Verify details are properly associated
        retrieved = repo.get_by_id_with_details("buy_order_cascade")

        assert len(retrieved.details) == 2
        assert retrieved.details[0].transaction_id == "buy_order_cascade"
        assert retrieved.details[1].transaction_id == "buy_order_cascade"
        assert retrieved.details[0].status == "AUTHORIZED"
        assert retrieved.details[1].status == "REJECTED"

    def test_get_all_transactions(self, db_session):
        """Test retrieving all transactions"""
        repo = TransactionRepository(db_session)

        # Create multiple transactions
        for i in range(5):
            transaction_data = {
                "id": f"buy_order_all_{i}",
                "username": f"testuser_all_{i}",
                "buy_order": f"buy_order_all_{i}"
            }
            repo.create(transaction_data)

        db_session.commit()

        transactions = repo.get_all(skip=0, limit=100)

        assert len(transactions) >= 5
        assert all(isinstance(t, OneclickTransaction) for t in transactions)

    def test_transaction_ordering_by_created_at(self, db_session):
        """Test that transactions are ordered by created_at DESC"""
        repo = TransactionRepository(db_session)

        # Create transactions with different timestamps
        import time
        for i in range(3):
            transaction_data = {
                "id": f"buy_order_time_{i}",
                "username": "testuser_ordering",
                "buy_order": f"buy_order_time_{i}"
            }
            repo.create(transaction_data)
            db_session.commit()
            time.sleep(0.01)  # Small delay to ensure different timestamps

        transactions = repo.get_by_username("testuser_ordering", skip=0, limit=10)

        # Most recent should be first (DESC order)
        assert len(transactions) == 3
        # Verify descending order by checking IDs (newest first)
        assert transactions[0].id == "buy_order_time_2"
        assert transactions[1].id == "buy_order_time_1"
        assert transactions[2].id == "buy_order_time_0"
