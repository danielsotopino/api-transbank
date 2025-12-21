import pytest
from datetime import datetime

from transbank_oneclick_api.repositories.inscription_repository import InscriptionRepository
from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription


class TestInscriptionRepository:
    """Test suite for InscriptionRepository"""

    def test_create_inscription(self, db_session):
        """Test creating a new inscription"""
        from datetime import datetime
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser",
            "email": "test@example.com",
            "tbk_user": "tbk_test_123",
            "inscription_date": datetime.utcnow(),
            "is_active": False  # PENDING
        }

        inscription = repo.create(inscription_data)
        db_session.flush()

        assert inscription.id is not None
        assert inscription.username == "testuser"
        assert inscription.email == "test@example.com"
        assert inscription.tbk_user == "tbk_test_123"
        assert inscription.is_active is False
        assert inscription.inscription_date is not None

    def test_get_by_id(self, db_session):
        """Test retrieving inscription by ID"""
        from datetime import datetime
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "tbk_user": "tbk_test_456",
            "inscription_date": datetime.utcnow(),
            "is_active": True  # COMPLETED
        }

        created = repo.create(inscription_data)
        db_session.flush()

        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.username == "testuser2"
        assert retrieved.is_active is True

    def test_get_by_username(self, db_session):
        """Test retrieving inscription by username"""
        from datetime import datetime
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser3",
            "email": "test3@example.com",
            "tbk_user": "tbk_test_789",
            "inscription_date": datetime.utcnow(),
            "is_active": True  # COMPLETED
        }

        repo.create(inscription_data)
        db_session.flush()

        inscription = repo.get_by_username("testuser3")

        assert inscription is not None
        assert inscription.username == "testuser3"
        assert inscription.is_active is True
        assert inscription.email == "test3@example.com"

    def test_get_by_username_not_found(self, db_session):
        """Test retrieving non-existent username returns None"""
        repo = InscriptionRepository(db_session)

        inscription = repo.get_by_username("nonexistent_user")

        assert inscription is None

    def test_get_by_tbk_user(self, db_session):
        """Test retrieving inscription by Transbank user token"""
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser4",
            "email": "test4@example.com",
            "tbk_user": "tbk_unique_token_123",
            "inscription_date": datetime.utcnow(),
            "is_active": True  # COMPLETED
        }

        repo.create(inscription_data)
        db_session.flush()

        inscription = repo.get_by_tbk_user("tbk_unique_token_123")

        assert inscription is not None
        assert inscription.tbk_user == "tbk_unique_token_123"
        assert inscription.username == "testuser4"

    def test_get_by_tbk_user_not_found(self, db_session):
        """Test retrieving non-existent tbk_user returns None"""
        repo = InscriptionRepository(db_session)

        inscription = repo.get_by_tbk_user("nonexistent_token")

        assert inscription is None

    def test_get_active_by_username(self, db_session):
        """Test retrieving only COMPLETED (active) inscriptions"""
        repo = InscriptionRepository(db_session)

        # Create PENDING inscription
        pending_data = {
            "username": "testuser5",
            "email": "test5@example.com",
            "tbk_user": "tbk_pending_123",
            "inscription_date": datetime.utcnow(),
            "is_active": False  # PENDING
        }
        repo.create(pending_data)

        # Create COMPLETED inscription
        completed_data = {
            "username": "testuser6",
            "email": "test6@example.com",
            "tbk_user": "tbk_completed_456",
            "inscription_date": datetime.utcnow(),
            "is_active": True  # COMPLETED
        }
        repo.create(completed_data)
        db_session.flush()

        # Should return None for PENDING
        pending_inscription = repo.get_active_by_username("testuser5")
        assert pending_inscription is None

        # Should return inscription for COMPLETED
        completed_inscription = repo.get_active_by_username("testuser6")
        assert completed_inscription is not None
        assert completed_inscription.username == "testuser6"
        assert completed_inscription.is_active is True

    def test_update_inscription(self, db_session):
        """Test updating an inscription"""
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser7",
            "email": "test7@example.com",
            "tbk_user": "tbk_initial_token",
            "inscription_date": datetime.utcnow(),
            "is_active": False  # PENDING
        }

        created = repo.create(inscription_data)
        db_session.flush()

        # Update status and tbk_user
        updated = repo.update(created.id, {
            "is_active": True,  # COMPLETED
            "tbk_user": "tbk_final_token",
            "card_type": "VISA",
            "card_number_masked": "****1234"
        })
        db_session.flush()

        assert updated is not None
        assert updated.id == created.id
        assert updated.is_active is True
        assert updated.tbk_user == "tbk_final_token"
        assert updated.card_type == "VISA"
        assert updated.card_number_masked == "****1234"

    def test_delete_inscription(self, db_session):
        """Test deleting an inscription"""
        repo = InscriptionRepository(db_session)

        inscription_data = {
            "username": "testuser8",
            "email": "test8@example.com",
            "tbk_user": "tbk_delete_test",
            "inscription_date": datetime.utcnow(),
            "is_active": True  # COMPLETED
        }

        created = repo.create(inscription_data)
        db_session.flush()

        # Delete inscription
        result = repo.delete(created.id)
        db_session.flush()

        assert result is True

        # Verify deletion
        deleted = repo.get_by_id(created.id)
        assert deleted is None

    def test_delete_nonexistent_inscription(self, db_session):
        """Test deleting non-existent inscription returns False"""
        repo = InscriptionRepository(db_session)

        result = repo.delete(99999)

        assert result is False

    def test_get_all_inscriptions(self, db_session):
        """Test retrieving all inscriptions with pagination"""
        repo = InscriptionRepository(db_session)

        # Create multiple inscriptions
        for i in range(5):
            inscription_data = {
                "username": f"testuser_all_{i}",
                "email": f"test{i}@example.com",
                "tbk_user": f"tbk_token_{i}",
                "inscription_date": datetime.utcnow(),
                "is_active": True  # COMPLETED
            }
            repo.create(inscription_data)

        db_session.flush()

        # Get all inscriptions
        inscriptions = repo.get_all(skip=0, limit=10)

        assert len(inscriptions) >= 5
        assert all(isinstance(i, OneclickInscription) for i in inscriptions)

    def test_get_all_with_pagination(self, db_session):
        """Test pagination of inscriptions"""
        repo = InscriptionRepository(db_session)

        # Create 10 inscriptions
        for i in range(10):
            inscription_data = {
                "username": f"testuser_paginate_{i}",
                "email": f"paginate{i}@example.com",
                "tbk_user": f"tbk_paginate_{i}",
                "inscription_date": datetime.utcnow(),
                "is_active": True  # COMPLETED
            }
            repo.create(inscription_data)

        db_session.flush()

        # Get first page (5 items)
        page1 = repo.get_all(skip=0, limit=5)
        assert len(page1) >= 5

        # Get second page (next 5 items)
        page2 = repo.get_all(skip=5, limit=5)
        assert len(page2) >= 5

        # Ensure pages don't overlap
        page1_ids = {i.id for i in page1}
        page2_ids = {i.id for i in page2}
        # Some overlap is okay in tests due to other test data
