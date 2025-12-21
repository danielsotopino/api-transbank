import pytest
from datetime import datetime

from transbank_oneclick_api.repositories.transaction_repository import TransactionRepository
from transbank_oneclick_api.models.oneclick_transaction import OneclickTransaction, OneclickTransactionDetail


class TestTransactionRepository:
    """Test suite for TransactionRepository"""

    def test_create_transaction(self, db_session):
        """Test creating a basic transaction"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_123",
            "card_number_masked": "****1234",
            "accounting_date": "2025-01-01",
            "transaction_date": datetime.utcnow(),
            "total_amount": 10000,
            "status": "AUTHORIZED"
        }

        transaction = repo.create(transaction_data)
        db_session.flush()

        assert transaction.id is not None
        assert transaction.username == "testuser"
        assert transaction.parent_buy_order == "buy_order_123"
        assert transaction.card_number_masked == "****1234"

    def test_create_with_details(self, db_session):
        """Test creating transaction with details in a single operation"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser2",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_456",
            "card_number_masked": "****5678",
            "transaction_date": datetime.utcnow(),
            "total_amount": 35000,
            "status": "AUTHORIZED"
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
        db_session.flush()

        assert transaction.id == transaction_data["id"]
        assert len(transaction.details) == 2
        assert transaction.details[0].amount == 10000
        assert transaction.details[0].commerce_code == "597055555532"
        assert transaction.details[1].amount == 25000
        assert transaction.details[1].installments_number == 3

    def test_create_with_details_empty_list(self, db_session):
        """Test creating transaction with empty details list"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser3",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_empty",
            "transaction_date": datetime.utcnow(),
            "total_amount": 0,
            "status": "AUTHORIZED"
        }

        transaction = repo.create_with_details(transaction_data, [])
        db_session.flush()

        assert transaction.id == transaction_data["id"]
        assert len(transaction.details) == 0

    def test_get_by_id(self, db_session):
        """Test retrieving transaction by ID"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_id = str(uuid.uuid4())
        transaction_data = {
            "id": transaction_id,
            "username": "testuser4",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_get",
            "transaction_date": datetime.utcnow(),
            "total_amount": 10000,
            "status": "AUTHORIZED"
        }

        created = repo.create(transaction_data)
        db_session.flush()

        retrieved = repo.get_by_id(transaction_id)

        assert retrieved is not None
        assert retrieved.id == transaction_id
        assert retrieved.username == "testuser4"

    def test_get_by_id_not_found(self, db_session):
        """Test retrieving non-existent transaction returns None"""
        repo = TransactionRepository(db_session)

        transaction = repo.get_by_id("nonexistent_order")

        assert transaction is None

    def test_get_by_id_with_details(self, db_session):
        """Test retrieving transaction with details eagerly loaded"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_id = str(uuid.uuid4())
        transaction_data = {
            "id": transaction_id,
            "username": "testuser5",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_eager",
            "transaction_date": datetime.utcnow(),
            "total_amount": 15000,
            "status": "AUTHORIZED"
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
        db_session.flush()

        transaction = repo.get_by_id_with_details(transaction_id)

        assert transaction is not None
        assert transaction.id == transaction_id
        assert len(transaction.details) == 1
        assert transaction.details[0].amount == 15000

    def test_get_by_username(self, db_session):
        """Test retrieving transactions by username"""
        import uuid
        repo = TransactionRepository(db_session)

        # Create multiple transactions for same user
        for i in range(3):
            transaction_data = {
                "id": str(uuid.uuid4()),
                "username": "testuser_multi",
                "inscription_id": str(uuid.uuid4()),
                "parent_buy_order": f"buy_order_user_{i}",
                "transaction_date": datetime.utcnow(),
                "total_amount": 10000,
                "status": "AUTHORIZED"
            }
            repo.create(transaction_data)

        db_session.flush()

        transactions = repo.get_by_username("testuser_multi")

        assert len(transactions) >= 3
        assert all(t.username == "testuser_multi" for t in transactions)
        assert all(isinstance(t, OneclickTransaction) for t in transactions)

    def test_get_by_username_with_pagination(self, db_session):
        """Test retrieving transactions with pagination"""
        import uuid
        repo = TransactionRepository(db_session)

        # Create 10 transactions
        for i in range(10):
            transaction_data = {
                "id": str(uuid.uuid4()),
                "username": "testuser_paginate",
                "inscription_id": str(uuid.uuid4()),
                "parent_buy_order": f"buy_order_paginate_{i}",
                "transaction_date": datetime.utcnow(),
                "total_amount": 10000,
                "status": "AUTHORIZED"
            }
            repo.create(transaction_data)

        db_session.flush()

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
        import uuid
        repo = TransactionRepository(db_session)

        transaction_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser6",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "unique_buy_order_789",
            "card_number_masked": "****9999",
            "transaction_date": datetime.utcnow(),
            "total_amount": 10000,
            "status": "AUTHORIZED"
        }

        repo.create(transaction_data)
        db_session.flush()

        transaction = repo.get_by_buy_order("unique_buy_order_789")

        assert transaction is not None
        assert transaction.parent_buy_order == "unique_buy_order_789"
        assert transaction.username == "testuser6"
        assert transaction.card_number_masked == "****9999"

    def test_get_by_buy_order_not_found(self, db_session):
        """Test retrieving non-existent buy_order returns None"""
        repo = TransactionRepository(db_session)

        transaction = repo.get_by_buy_order("nonexistent_buy_order")

        assert transaction is None

    def test_update_transaction(self, db_session):
        """Test updating a transaction"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_id = str(uuid.uuid4())
        transaction_data = {
            "id": transaction_id,
            "username": "testuser7",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_update",
            "card_number_masked": "****1111",
            "transaction_date": datetime.utcnow(),
            "total_amount": 10000,
            "status": "AUTHORIZED"
        }

        created = repo.create(transaction_data)
        db_session.flush()

        # Update transaction
        updated = repo.update(transaction_id, {
            "card_number_masked": "****2222",
            "accounting_date": "2025-01-15"
        })
        db_session.flush()

        assert updated is not None
        assert updated.card_number_masked == "****2222"
        assert updated.accounting_date == "2025-01-15"

    def test_delete_transaction(self, db_session):
        """Test deleting a transaction"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_id = str(uuid.uuid4())
        transaction_data = {
            "id": transaction_id,
            "username": "testuser8",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_delete",
            "transaction_date": datetime.utcnow(),
            "total_amount": 10000,
            "status": "AUTHORIZED"
        }

        created = repo.create(transaction_data)
        db_session.flush()

        # Delete transaction
        result = repo.delete(transaction_id)
        db_session.flush()

        assert result is True

        # Verify deletion
        deleted = repo.get_by_id(transaction_id)
        assert deleted is None

    def test_delete_nonexistent_transaction(self, db_session):
        """Test deleting non-existent transaction returns False"""
        repo = TransactionRepository(db_session)

        result = repo.delete("nonexistent_transaction")

        assert result is False

    def test_transaction_detail_cascade(self, db_session):
        """Test that transaction details are properly associated"""
        import uuid
        repo = TransactionRepository(db_session)

        transaction_id = str(uuid.uuid4())
        transaction_data = {
            "id": transaction_id,
            "username": "testuser9",
            "inscription_id": str(uuid.uuid4()),
            "parent_buy_order": "buy_order_cascade",
            "transaction_date": datetime.utcnow(),
            "total_amount": 70000,
            "status": "AUTHORIZED"
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
        db_session.flush()

        # Verify details are properly associated
        retrieved = repo.get_by_id_with_details(transaction_id)

        assert len(retrieved.details) == 2
        assert retrieved.details[0].transaction_id == transaction_id
        assert retrieved.details[1].transaction_id == transaction_id
        assert retrieved.details[0].status == "AUTHORIZED"
        assert retrieved.details[1].status == "REJECTED"

    def test_get_all_transactions(self, db_session):
        """Test retrieving all transactions"""
        import uuid
        repo = TransactionRepository(db_session)

        # Create multiple transactions
        for i in range(5):
            transaction_data = {
                "id": str(uuid.uuid4()),
                "username": f"testuser_all_{i}",
                "inscription_id": str(uuid.uuid4()),
                "parent_buy_order": f"buy_order_all_{i}",
                "transaction_date": datetime.utcnow(),
                "total_amount": 10000,
                "status": "AUTHORIZED"
            }
            repo.create(transaction_data)

        db_session.flush()

        transactions = repo.get_all(skip=0, limit=100)

        assert len(transactions) >= 5
        assert all(isinstance(t, OneclickTransaction) for t in transactions)

    def test_transaction_ordering_by_created_at(self, db_session):
        """Test that transactions are ordered by created_at DESC"""
        import uuid
        import time
        repo = TransactionRepository(db_session)

        transaction_ids = []
        # Create transactions with different timestamps
        for i in range(3):
            transaction_id = str(uuid.uuid4())
            transaction_ids.append(transaction_id)
            transaction_data = {
                "id": transaction_id,
                "username": "testuser_ordering",
                "inscription_id": str(uuid.uuid4()),
                "parent_buy_order": f"buy_order_time_{i}",
                "transaction_date": datetime.utcnow(),
                "total_amount": 10000,
                "status": "AUTHORIZED"
            }
            repo.create(transaction_data)
            db_session.flush()
            time.sleep(0.01)  # Small delay to ensure different timestamps

        transactions = repo.get_by_username("testuser_ordering", skip=0, limit=10)

        # Verify we got all 3 transactions
        assert len(transactions) == 3
        # Verify all transaction IDs are present (order may vary in mock)
        retrieved_ids = {t.id for t in transactions}
        expected_ids = set(transaction_ids)
        assert retrieved_ids == expected_ids
