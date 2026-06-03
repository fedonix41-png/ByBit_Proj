"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment
os.environ["USE_AI_MOCK"] = "true"
os.environ["USE_MOCK_DATA"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.USE_AI_MOCK = True
    settings.USE_MOCK_DATA = True
    settings.AI_PROVIDER = "mock"
    return settings


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_bybit_client():
    """Mock Bybit API client."""
    client = MagicMock()
    # These methods are synchronous in BybitClient
    client.get_ads_list = MagicMock(return_value=[])
    client.create_ad = MagicMock(return_value="AD_123")
    client.get_online_ads = MagicMock(return_value=[])
    client.get_ad_details = MagicMock(return_value={"ad_id": "AD_123"})
    client.update_ad = MagicMock(return_value=True)
    client.cancel_order = MagicMock(return_value=True)
    client.get_chat_messages = MagicMock(return_value=[])
    client.send_chat_message = MagicMock(return_value=True)
    client.get_balance = MagicMock(return_value=[])
    client.get_payment_methods = MagicMock(return_value=[])
    client.get_account_information = MagicMock(return_value={"memberId": "test"})
    client.get_counterparty_info = MagicMock(return_value={"nickname": "TestUser"})
    client.get_order_details = MagicMock(return_value={"order_id": "TEST-ORDER-123"})
    client.confirm_payment = MagicMock(return_value=True)
    client.get_trade_history = MagicMock(return_value=[])
    client.get_orders = MagicMock(return_value=[])
    client.get_pending_orders = MagicMock(return_value=[])
    client.mark_as_paid = MagicMock(return_value=True)
    client.release_assets = MagicMock(return_value=True)
    return client


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    from app.database.security_models import User
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        password_hash="fake_hash",
        role="user",
        is_active=True
    )


@pytest.fixture
def test_client(mock_user, mock_bybit_client):
    """Test client for FastAPI app with overridden dependencies."""
    from fastapi.testclient import TestClient
    from server import app
    from app.core import get_current_user

    # Override authentication
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Patch the global bybit_client instance in server.py
    with patch("server.bybit_client", mock_bybit_client):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Headers for authorized requests (though get_current_user is overridden)."""
    return {"Authorization": "Bearer mock_token"}


@pytest.fixture
def sample_order_data():
    """Sample order data for tests."""
    return {
        "order_id": "TEST-ORDER-123",
        "ad_id": "TEST-AD-456",
        "side": "BUY",
        "crypto": "USDT",
        "currency": "RUB",
        "amount": 10000.0,
        "price": 95.0,
        "status": "pending",
        "counterparty": "test_user",
        "created_at": "2024-01-15T14:00:00Z"
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data for tests."""
    return {
        "amount": 10000.0,
        "currency": "RUB",
        "card_number": "4276****5678",
        "timestamp": "2024-01-15T14:30:00",
        "bank": "Сбербанк"
    }
