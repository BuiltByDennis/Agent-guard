import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from database import get_db
from models import User
from auth import get_password_hash

# We will mock the database and redis for these integration tests
async def override_get_db():
    class MockResult:
        def __init__(self, user):
            self.user = user
        def scalar_one_or_none(self):
            return self.user

    class MockSession:
        async def execute(self, stmt):
            # Check if it's querying for the test user
            return MockResult(test_user)
            
    yield MockSession()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# A fake user for the mock DB
test_user = User(
    id="user-123",
    email="admin@example.com",
    hashed_password=get_password_hash("SuperSecret1!"),
    role="admin",
    is_active=True
)

@patch("routers.auth.get_redis")
def test_auth_flow_integration(mock_get_redis):
    # Mock redis to bypass lockout and blocklist
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_redis.return_value = mock_redis
    
    # 1. Login to get tokens
    response = client.post("/v1/auth/token", data={
        "username": "admin@example.com",
        "password": "SuperSecret1!"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert "csrf_token" in response.cookies
    
    # 2. Access protected endpoint (Admin Users Me)
    # We need to simulate the browser sending cookies AND the CSRF token
    cookies = response.cookies
    csrf_token = cookies.get("csrf_token")
    
    # Also we need to mock DB for the 'me' endpoint if it queries, but /v1/admin/users/me just returns the current_user from token
    # Wait, get_current_user queries the DB.
    me_response = client.get("/v1/admin/users/me", cookies=cookies)
    
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"
    
    # 3. Test token refresh
    # For POST /refresh, we need CSRF header
    refresh_response = client.post(
        "/v1/auth/refresh",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token}
    )
    
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.cookies
    
    # 4. Test Logout
    logout_response = client.post(
        "/v1/auth/logout",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token}
    )
    
    assert logout_response.status_code == 200
    # Cookies should be empty or expired
    assert not logout_response.cookies.get("access_token")
