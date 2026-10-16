import time
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app

client = TestClient(app)


def test_invalid_json_payload():
    # Sending malformed JSON
    response = client.post(
        "/v1/admin/agents",
        content="{invalid json:",
        headers={"Content-Type": "application/json"},
    )

    # FastAPI automatically handles invalid JSON and returns 422
    assert response.status_code == 422


def test_expired_jwt():
    # Create an expired token
    expired_token = jwt.encode(
        {"sub": "admin@example.com", "exp": int(time.time()) - 3600, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    # Hit an endpoint protected by get_current_user with all dependency
    # overrides removed, then restore them so later test modules are
    # unaffected.
    saved_overrides = dict(app.dependency_overrides)
    app.dependency_overrides = {}
    try:
        response = client.get(
            "/v1/admin/users/me", cookies={"access_token": expired_token}
        )
    finally:
        app.dependency_overrides = saved_overrides

    assert response.status_code == 401


@pytest.mark.asyncio
@patch("services.telemetry.get_redis")
@patch("services.telemetry.AsyncSessionLocal")
async def test_redis_fallback_on_db_failure(mock_db, mock_get_redis):
    from services.telemetry import save_interaction_to_db

    # Make DB raise an exception
    mock_db.side_effect = Exception("DB Connection Failed")

    # Mock Redis client
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis

    span_data = {"agent_id": "test", "latency_ms": 100}

    # Call the save function
    await save_interaction_to_db(span_data)

    # Assert DB failed but Redis lpush was called
    mock_redis.lpush.assert_called_once()
