import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from transbank_oneclick_api.main import app
from transbank_oneclick_api.database import Base, get_db
from transbank_oneclick_api.config import settings


# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_setup():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test database
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def db_session(db_setup):
    """Create a test database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


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