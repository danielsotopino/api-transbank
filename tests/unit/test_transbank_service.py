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
        mock_response = Mock()
        mock_response.token = "test_token_123"
        mock_response.url_webpay = "https://webpay.transbank.cl/test"
        mock_start.return_value = mock_response
        
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
        mock_response = Mock()
        mock_response.response_code = 0
        mock_response.tbk_user = "user_token_123"
        mock_response.authorization_code = "auth_123"
        mock_response.card_type = "VISA"
        mock_response.card_number = "XXXX-XXXX-XXXX-1234"
        mock_finish.return_value = mock_response
        
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
        mock_response = Mock()
        mock_response.response_code = -1
        mock_finish.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(TransactionRejectedException):
            await transbank_service.finish_inscription(token="test_token")
    
    @patch('app.services.transbank_service.MallTransaction.authorize')
    @pytest.mark.asyncio
    async def test_authorize_transaction_success(self, mock_authorize, transbank_service):
        # Arrange
        mock_detail = Mock()
        mock_detail.amount = 10000
        mock_detail.response_code = 0
        mock_detail.status = "approved"
        mock_detail.authorization_code = "auth_123"
        mock_detail.payment_type_code = "VN"
        mock_detail.installments_number = 1
        mock_detail.commerce_code = "597055555542"
        mock_detail.buy_order = "order_123"
        
        mock_response = Mock()
        mock_response.parent_buy_order = "parent_order_123"
        mock_response.session_id = "session_123"
        mock_response.card_detail.card_number = "XXXX-XXXX-XXXX-1234"
        mock_response.accounting_date = "0320"
        mock_response.transaction_date = MagicMock()
        mock_response.transaction_date.isoformat.return_value = "2023-03-20T10:30:00"
        mock_response.details = [mock_detail]
        
        mock_authorize.return_value = mock_response
        
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
        mock_detail = Mock()
        mock_detail.amount = 10000
        mock_detail.response_code = 0
        mock_detail.status = "approved"
        mock_detail.authorization_code = "auth_123"
        mock_detail.payment_type_code = "VN"
        mock_detail.installments_number = 1
        mock_detail.commerce_code = "597055555542"
        mock_detail.buy_order = "order_123"
        mock_detail.balance = 0
        
        mock_response = Mock()
        mock_response.buy_order = "order_123"
        mock_response.session_id = "session_123"
        mock_response.card_detail.card_number = "XXXX-XXXX-XXXX-1234"
        mock_response.accounting_date = "0320"
        mock_response.transaction_date = MagicMock()
        mock_response.transaction_date.isoformat.return_value = "2023-03-20T10:30:00"
        mock_response.details = [mock_detail]
        
        mock_status.return_value = mock_response
        
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