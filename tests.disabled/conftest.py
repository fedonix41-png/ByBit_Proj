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
    client.get_ads_list = AsyncMock(return_value={"result": {"items": []}})
    client.send_message = AsyncMock(return_value={"result": {}})
    client.get_account_information = AsyncMock(return_value={"result": {"memberId": "test"}})
    return client


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
