import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestInscriptionAPI:
    
    @patch('transbank_oneclick_api.services.transbank_service.MallInscription.start')
    def test_start_inscription_success(self, mock_start, client, sample_inscription_data):
        # Arrange
        mock_start.return_value = {
            "token": "test_token_123",
            "url_webpay": "https://webpay.transbank.cl/test"
        }
        
        # Act
        response = client.post(
            "/api/v1/oneclick/mall/inscription/start",
            json=sample_inscription_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["token"] == "test_token_123"
        assert data["data"]["url_webpay"] == "https://webpay.transbank.cl/test"
        assert data["errors"] == []
    
    def test_start_inscription_validation_error(self, client):
        # Arrange
        invalid_data = {
            "username": "",  # Invalid: empty username
            "email": "invalid-email",  # Invalid: not a valid email
            "response_url": "not-a-url"  # Invalid: not a valid URL
        }
        
        # Act
        response = client.post(
            "/api/v1/oneclick/mall/inscription/start",
            json=invalid_data
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
    
    @patch('transbank_oneclick_api.services.transbank_service.MallInscription.finish')
    def test_finish_inscription_success(self, mock_finish, client, db_session):
        # Arrange
        mock_finish.return_value = {
            "response_code": 0,
            "tbk_user": "user_token_123",
            "authorization_code": "auth_123",
            "card_type": "VISA",
            "card_number": "XXXX-XXXX-XXXX-1234"
        }
        
        finish_data = {"token": "test_token_123", "username": "testuser"}
        
        # Act
        response = client.put(
            "/api/v1/oneclick/mall/inscription/finish",
            json=finish_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["response_code"] == 0
        assert data["data"]["tbk_user"] == "user_token_123"
        assert data["data"]["card_type"] == "VISA"
    
    def test_list_inscriptions_empty(self, client):
        # Act
        response = client.get("/api/v1/oneclick/mall/inscription/testuser")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["inscriptions"] == []
        assert data["data"]["total_inscriptions"] == 0


class TestTransactionAPI:
    
    @patch('transbank_oneclick_api.services.transbank_service.MallTransaction.authorize')
    def test_authorize_transaction_success(self, mock_authorize, client, db_session, sample_transaction_data):
        # Arrange - First create a mock inscription
        from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription
        import uuid
        from datetime import datetime
        
        inscription = OneclickInscription(
            id=str(uuid.uuid4()),
            username=sample_transaction_data["username"],
            email="test@example.com",
            tbk_user=sample_transaction_data["tbk_user"],
            card_type="VISA",
            card_number_masked="XXXX-XXXX-XXXX-1234",
            authorization_code="auth_123",
            inscription_date=datetime.utcnow(),
            is_active=True
        )
        db_session.add(inscription)
        db_session.commit()
        
        # Mock Transbank response
        mock_authorize.return_value = {
            "parent_buy_order": sample_transaction_data["parent_buy_order"],
            "session_id": "session_123",
            "card_detail": {"card_number": "XXXX-XXXX-XXXX-1234"},
            "accounting_date": "0320",
            "transaction_date": type("dt", (), {"isoformat": lambda self: "2023-03-20T10:30:00Z"})(),
            "details": [
                {
                    "amount": 10000,
                    "response_code": 0,
                    "status": "approved",
                    "authorization_code": "auth_123",
                    "payment_type_code": "VN",
                    "installments_number": 1,
                    "commerce_code": "597055555542",
                    "buy_order": "child_order_1"
                }
            ]
        }
        
        # Act
        response = client.post(
            "/api/v1/oneclick/mall/transaction/authorize",
            json=sample_transaction_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["parent_buy_order"] == sample_transaction_data["parent_buy_order"]
        assert data["data"]["session_id"] == "session_123"
        assert len(data["data"]["details"]) == 1
        assert data["data"]["details"][0]["status"] == "approved"
    
    def test_authorize_transaction_duplicate_order(self, client, db_session, sample_transaction_data):
        # Arrange - Create an inscription and existing transaction
        from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription
        from transbank_oneclick_api.models.oneclick_transaction import OneclickTransaction
        import uuid
        from datetime import datetime
        
        inscription = OneclickInscription(
            id=str(uuid.uuid4()),
            username=sample_transaction_data["username"],
            email="test@example.com",
            tbk_user=sample_transaction_data["tbk_user"],
            card_type="VISA",
            card_number_masked="XXXX-XXXX-XXXX-1234",
            authorization_code="auth_123",
            inscription_date=datetime.utcnow(),
            is_active=True
        )
        db_session.add(inscription)
        db_session.flush()
        
        existing_transaction = OneclickTransaction(
            id=str(uuid.uuid4()),
            username=sample_transaction_data["username"],
            inscription_id=inscription.id,
            parent_buy_order=sample_transaction_data["parent_buy_order"],
            session_id="existing_session",
            transaction_date=datetime.utcnow(),
            accounting_date="0320",
            total_amount=35000,
            card_number_masked="XXXX-XXXX-XXXX-1234",
            status="processed"
        )
        db_session.add(existing_transaction)
        db_session.commit()
        
        # Act
        response = client.post(
            "/api/v1/oneclick/mall/transaction/authorize",
            json=sample_transaction_data
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert any("ORDEN_COMPRA_DUPLICADA" in error["code"] for error in data["errors"])
    
    def test_transaction_history_empty(self, client):
        # Act
        response = client.get("/api/v1/oneclick/mall/transaction/history/testuser")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["transactions"] == []
        assert data["data"]["pagination"]["total"] == 0


class TestHealthCheck:
    
    def test_root_endpoint(self, client):
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "environment" in data
    
    def test_health_endpoint(self, client):
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "service" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]