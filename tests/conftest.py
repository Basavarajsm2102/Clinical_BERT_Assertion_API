import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture  
def mock_model():
    mock = Mock()
    mock.is_loaded.return_value = True
    mock.predict = AsyncMock(return_value={"label": "ABSENT", "score": 0.9842})
    mock.predict_batch = AsyncMock(return_value=[{"label": "ABSENT", "score": 0.9842}])
    return mock
