import pytest
from unittest.mock import MagicMock, Mock
from fastapi.testclient import TestClient
from collections import defaultdict

from transbank_oneclick_api.main import app
from transbank_oneclick_api.database import get_db


class MockQuery:
    """Mock query object that simulates SQLAlchemy query behavior"""
    def __init__(self, model_class, storage):
        self.model_class = model_class
        self.storage = storage
        self._filters = []
        self._limit = None
        self._offset = None
        self._order_by = None
    
    def filter(self, *args, **kwargs):
        """Add filter conditions"""
        self._filters.append((args, kwargs))
        return self
    
    def limit(self, value):
        """Set limit"""
        self._limit = value
        return self
    
    def offset(self, value):
        """Set offset"""
        self._offset = value
        return self
    
    def order_by(self, *args):
        """Set order by"""
        self._order_by = args
        return self
    
    def options(self, *args):
        """Set query options (for eager loading)"""
        return self
    
    def first(self):
        """Return first matching result"""
        results = self._get_results()
        return results[0] if results else None
    
    def all(self):
        """Return all matching results"""
        results = self._get_results()
        if self._limit is not None:
            start = self._offset or 0
            end = start + self._limit
            return results[start:end]
        return results
    
    def count(self):
        """Return count of matching results"""
        return len(self._get_results())
    
    def _get_results(self):
        """Get results based on filters"""
        model_name = self.model_class.__name__
        if model_name not in self.storage:
            return []
        
        all_items = list(self.storage[model_name].values())
        
        # Apply filters
        for filter_args, filter_kwargs in self._filters:
            filtered_items = []
            for item in all_items:
                match = True
                # Handle filter arguments (like Model.column == value or Model.column)
                for filter_arg in filter_args:
                    # Check if it's a comparison operation
                    if hasattr(filter_arg, 'left') and hasattr(filter_arg, 'right'):
                        # SQLAlchemy comparison like Model.column == value
                        attr_name = filter_arg.left.key if hasattr(filter_arg.left, 'key') else None
                        if attr_name and hasattr(item, attr_name):
                            # Get the right side value - handle both direct values and SQLAlchemy objects
                            right_value = filter_arg.right
                            if hasattr(right_value, 'value'):
                                right_value = right_value.value
                            elif hasattr(right_value, '__bool__'):
                                right_value = bool(right_value)
                            
                            if getattr(item, attr_name) != right_value:
                                match = False
                                break
                    elif hasattr(filter_arg, 'key'):
                        # Direct attribute filter like Model.column (for boolean checks)
                        attr_name = filter_arg.key
                        if hasattr(item, attr_name):
                            # For boolean attributes, check if it's True
                            if not getattr(item, attr_name):
                                match = False
                                break
                # Handle keyword arguments
                for key, value in filter_kwargs.items():
                    if hasattr(item, key):
                        if getattr(item, key) != value:
                            match = False
                            break
                if match:
                    filtered_items.append(item)
            all_items = filtered_items
        
        return all_items


@pytest.fixture
def db_session():
    """Create a mock database session using MagicMock with in-memory storage"""
    session = MagicMock()
    
    # In-memory storage for testing
    storage = defaultdict(dict)
    added_objects = []
    
    def query_side_effect(model_class):
        return MockQuery(model_class, storage)
    
    session.query = Mock(side_effect=query_side_effect)
    
    def add_side_effect(obj):
        """Store object in memory"""
        if hasattr(obj, '__class__'):
            model_name = obj.__class__.__name__
            if not hasattr(obj, 'id') or obj.id is None:
                import uuid
                obj.id = str(uuid.uuid4())
            storage[model_name][obj.id] = obj
            added_objects.append(obj)
            
            # Handle relationships - if object has transaction_id, associate with transaction
            if hasattr(obj, 'transaction_id') and obj.transaction_id:
                transaction_model_name = 'OneclickTransaction'
                if transaction_model_name in storage and obj.transaction_id in storage[transaction_model_name]:
                    transaction = storage[transaction_model_name][obj.transaction_id]
                    if hasattr(transaction, 'details') and not hasattr(transaction.details, '__call__'):
                        if not hasattr(transaction, '_details_initialized'):
                            transaction.details = []
                            transaction._details_initialized = True
                        transaction.details.append(obj)
    
    def refresh_side_effect(obj):
        """Refresh object from storage"""
        if hasattr(obj, '__class__') and hasattr(obj, 'id'):
            model_name = obj.__class__.__name__
            if obj.id in storage[model_name]:
                stored_obj = storage[model_name][obj.id]
                for attr in dir(stored_obj):
                    if not attr.startswith('_'):
                        try:
                            setattr(obj, attr, getattr(stored_obj, attr))
                        except:
                            pass
    
    def delete_side_effect(obj):
        """Remove object from storage"""
        if hasattr(obj, '__class__') and hasattr(obj, 'id'):
            model_name = obj.__class__.__name__
            if obj.id in storage[model_name]:
                del storage[model_name][obj.id]
    
    # Mock session methods
    session.add = Mock(side_effect=add_side_effect)
    session.delete = Mock(side_effect=delete_side_effect)
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.merge = Mock(side_effect=lambda x: x)
    session.flush = Mock()
    session.refresh = Mock(side_effect=refresh_side_effect)
    
    # Store storage and added_objects for test access
    session._storage = storage
    session._added_objects = added_objects
    
    yield session
    
    # Cleanup
    storage.clear()
    added_objects.clear()


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_inscription_data():
    """Sample data for inscription tests"""
    return {
        "username": "testuser123",
        "email": "test@example.com",
        "response_url": "https://example.com/callback"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample data for transaction tests"""
    return {
        "username": "testuser123",
        "tbk_user": "test_tbk_user_token",
        "parent_buy_order": "parent_order_123",
        "details": [
            {
                "commerce_code": "597055555542",
                "buy_order": "child_order_1",
                "amount": 10000,
                "installments_number": 1
            },
            {
                "commerce_code": "597055555543",
                "buy_order": "child_order_2",
                "amount": 25000,
                "installments_number": 3
            }
        ]
    }