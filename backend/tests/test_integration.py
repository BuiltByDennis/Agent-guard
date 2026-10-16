from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from auth import get_password_hash
from database import get_db
from main import app
from models import User

# A fake user for the mock DB
test_user = User(
    id="user-123",
    email="admin@example.com",
    hashed_password=get_password_hash("SuperSecret1!"),
    role="admin",
)


# We will mock the database and redis for these integration tests
async def override_get_db():
    class MockResult:
        def __init__(self, user):
            self.user = user

        def scalar_one_or_none(self):
            return self.user

    class MockSession:
        async def execute(self, stmt):
            # Any user query returns the test user
            return MockResult(test_user)

    yield MockSession()


client = TestClient(app)


@patch("routers.auth.get_redis")
def test_auth_flow_integration(mock_get_redis):
    # Install this module's DB override inside the test so it does not
    # depend on import order across test modules sharing one app.
    app.dependency_overrides[get_db] = override_get_db

    # Mock redis to bypass lockout and blocklist
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_redis.return_value = mock_redis

    # 1. Login to get tokens
    response = client.post(
        "/v1/auth/token",
        data={"username": "admin@example.com", "password": "SuperSecret1!"},
    )

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert "csrf_token" in response.cookies

    # 2. Access protected endpoint (current user profile)
    # Build a plain dict: passing httpx's response.cookies object directly
    # drops Secure cookies when the test server URL is plain http.
    cookies = {
        name: response.cookies.get(name)
        for name in ("access_token", "refresh_token", "csrf_token")
    }
    csrf_token = cookies["csrf_token"]

    me_response = client.get("/v1/admin/users/me", cookies=cookies)

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"

    # 3. Test token refresh
    refresh_response = client.post(
        "/v1/auth/refresh",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.cookies

    # 4. Test Logout
    logout_response = client.post(
        "/v1/auth/logout",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token},
    )

    assert logout_response.status_code == 200
    # Cookies should be empty or expired
    assert not logout_response.cookies.get("access_token")
