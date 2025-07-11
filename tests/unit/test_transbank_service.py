import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.transbank_service import TransbankService
from app.core.exceptions import TransbankCommunicationException, TransactionRejectedException


class TestTransbankService:
    
    @pytest.fixture
    def transbank_service(self):
        return TransbankService()
    
    @patch('app.services.transbank_service.MallInscription.start')
    @pytest.mark.asyncio
    async def test_start_inscription_success(self, mock_start, transbank_service):
        # Arrange
        mock_start.return_value = {
            "token": "test_token_123",
            "url_webpay": "https://webpay.transbank.cl/test"
        }
        
        # Act
        result = await transbank_service.start_inscription(
            username="testuser",
            email="test@example.com",
            response_url="https://example.com/callback"
        )
        
        # Assert
        assert result["token"] == "test_token_123"
        assert result["url_webpay"] == "https://webpay.transbank.cl/test"
        mock_start.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            response_url="https://example.com/callback"
        )
    
    @patch('app.services.transbank_service.MallInscription.start')
    @pytest.mark.asyncio
    async def test_start_inscription_error(self, mock_start, transbank_service):
        # Arrange
        mock_start.side_effect = Exception("Connection error")
        
        # Act & Assert
        with pytest.raises(TransbankCommunicationException):
            await transbank_service.start_inscription(
                username="testuser",
                email="test@example.com",
                response_url="https://example.com/callback"
            )
    
    @patch('app.services.transbank_service.MallInscription.finish')
    @pytest.mark.asyncio
    async def test_finish_inscription_success(self, mock_finish, transbank_service):
        # Arrange
        mock_finish.return_value = {
            "response_code": 0,
            "tbk_user": "user_token_123",
            "authorization_code": "auth_123",
            "card_type": "VISA",
            "card_number": "XXXX-XXXX-XXXX-1234"
        }
        
        # Act
        result = await transbank_service.finish_inscription(token="test_token")
        
        # Assert
        assert result["response_code"] == 0
        assert result["tbk_user"] == "user_token_123"
        assert result["card_type"] == "VISA"
        mock_finish.assert_called_once_with("test_token")
    
    @patch('app.services.transbank_service.MallInscription.finish')
    @pytest.mark.asyncio
    async def test_finish_inscription_rejected(self, mock_finish, transbank_service):
        # Arrange
        mock_finish.return_value = {
            "response_code": -1
        }
        
        # Act & Assert
        with pytest.raises(TransactionRejectedException):
            await transbank_service.finish_inscription(token="test_token")
    
    @patch('app.services.transbank_service.MallTransaction.authorize')
    @pytest.mark.asyncio
    async def test_authorize_transaction_success(self, mock_authorize, transbank_service):
        # Arrange
        mock_authorize.return_value = {
            "parent_buy_order": "parent_order_123",
            "session_id": "session_123",
            "card_detail": {"card_number": "XXXX-XXXX-XXXX-1234"},
            "accounting_date": "0320",
            "transaction_date": type("dt", (), {"isoformat": lambda self: "2023-03-20T10:30:00"})(),
            "details": [
                {
                    "amount": 10000,
                    "response_code": 0,
                    "status": "approved",
                    "authorization_code": "auth_123",
                    "payment_type_code": "VN",
                    "installments_number": 1,
                    "commerce_code": "597055555542",
                    "buy_order": "order_123"
                }
            ]
        }
        
        details = [{
            "commerce_code": "597055555542",
            "buy_order": "order_123",
            "amount": 10000,
            "installments_number": 1
        }]
        
        # Act
        result = await transbank_service.authorize_transaction(
            username="testuser",
            tbk_user="user_token",
            parent_buy_order="parent_order_123",
            details=details
        )
        
        # Assert
        assert result["parent_buy_order"] == "parent_order_123"
        assert result["session_id"] == "session_123"
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "approved"
        assert result["details"][0]["response_code"] == 0
    
    @patch('app.services.transbank_service.MallInscription.delete')
    @pytest.mark.asyncio
    async def test_delete_inscription_success(self, mock_delete, transbank_service):
        # Arrange
        mock_delete.return_value = Mock()
        
        # Act
        result = await transbank_service.delete_inscription(
            tbk_user="user_token",
            username="testuser"
        )
        
        # Assert
        assert result["deleted"] is True
        mock_delete.assert_called_once_with("user_token", "testuser")
    
    @patch('app.services.transbank_service.MallTransaction.status')
    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, mock_status, transbank_service):
        # Arrange
        mock_status.return_value = {
            "buy_order": "order_123",
            "session_id": "session_123",
            "card_detail": {"card_number": "XXXX-XXXX-XXXX-1234"},
            "accounting_date": "0320",
            "transaction_date": type("dt", (), {"isoformat": lambda self: "2023-03-20T10:30:00"})(),
            "details": [
                {
                    "amount": 10000,
                    "response_code": 0,
                    "status": "approved",
                    "authorization_code": "auth_123",
                    "payment_type_code": "VN",
                    "installments_number": 1,
                    "commerce_code": "597055555542",
                    "buy_order": "order_123",
                    "balance": 0
                }
            ]
        }
        
        # Act
        result = await transbank_service.get_transaction_status(
            child_buy_order="order_123",
            child_commerce_code="597055555542"
        )
        
        # Assert
        assert result["buy_order"] == "order_123"
        assert result["session_id"] == "session_123"
        assert len(result["details"]) == 1
        mock_status.assert_called_once_with(
            buy_order="order_123"
        )