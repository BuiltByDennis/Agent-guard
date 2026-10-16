from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from core.config import settings
from core.dependencies import get_rate_limit_key
from services.firewall import scan_and_redact
from services.velocity import check_cost_velocity


# --- Firewall / Redact Tests ---
def test_scan_and_redact_no_violations():
    text = "Hello world, this is a normal message."
    redacted, has_violation = scan_and_redact(text)
    assert not has_violation
    assert redacted == text


def test_scan_and_redact_with_ssn():
    text = "My SSN is 123-45-6789."
    # Temporary mock settings to SANITIZE
    settings.FIREWALL_MODE = "SANITIZE"
    redacted, has_violation = scan_and_redact(text)
    assert has_violation
    assert "123-45-6789" not in redacted
    assert "[REDACTED_BY_FIREWALL]" in redacted


def test_scan_and_redact_with_api_key():
    text = "Here is my key: sk-1234567890abcdef1234567890abcdef1234567890abcdef1."
    settings.FIREWALL_MODE = "SANITIZE"
    redacted, has_violation = scan_and_redact(text)
    assert has_violation
    assert "sk-" not in redacted


# --- Velocity Tests ---
# check_cost_velocity runs an atomic Lua script via Redis EVAL: it returns 1
# when the new cost would exceed the limit (and does not increment), or 0
# after incrementing. The tests mock that EVAL contract.
@pytest.mark.asyncio
@patch("services.velocity.get_redis")
async def test_check_cost_velocity_under_limit(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis

    # Lua script reports "not exceeded" and records the cost
    mock_redis.eval.return_value = 0
    settings.VELOCITY_LIMIT = 10.0

    exceeded = await check_cost_velocity("agent-123", 1.0)
    assert not exceeded
    mock_redis.eval.assert_called_once()


@pytest.mark.asyncio
@patch("services.velocity.get_redis")
async def test_check_cost_velocity_over_limit(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis

    # Lua script reports "exceeded" (cost not recorded)
    mock_redis.eval.return_value = 1
    settings.VELOCITY_LIMIT = 10.0

    exceeded = await check_cost_velocity("agent-123", 1.0)
    assert exceeded
    mock_redis.eval.assert_called_once()


# --- Rate Limit Key Tests ---
def test_get_rate_limit_key_with_auth():
    request = MagicMock()
    token = jwt.encode(
        {"sub": "user-123"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    request.headers.get.side_effect = lambda k: (
        f"Bearer {token}" if k == "Authorization" else None
    )

    key = get_rate_limit_key(request)
    assert key == "user-123"


def test_get_rate_limit_key_with_forwarded_for():
    request = MagicMock()
    request.headers.get.side_effect = lambda k: (
        "192.168.1.1, 10.0.0.1" if k == "X-Forwarded-For" else None
    )

    key = get_rate_limit_key(request)
    assert key == "192.168.1.1"


def test_get_rate_limit_key_fallback_ip():
    request = MagicMock()
    request.headers.get.return_value = None
    request.client.host = "10.0.0.5"

    key = get_rate_limit_key(request)
    assert key == "10.0.0.5"
