import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from database import get_db_with_rls
from auth import require_admin
from models import User

# Mock DB and Admin
async def override_get_db_with_rls():
    class MockSession:
        async def execute(self, *args, **kwargs):
            class MockResult:
                def scalar_one_or_none(self):
                    return True
                def scalars(self):
                    class Scalars:
                        def all(self):
                            return []
                    return Scalars()
            return MockResult()
        
        def add(self, *args, **kwargs):
            pass
            
        async def commit(self):
            pass
            
        async def rollback(self):
            pass
            
    yield MockSession()

async def override_require_admin():
    return User(id="admin-123", email="admin@example.com", role="admin")

app.dependency_overrides[get_db_with_rls] = override_get_db_with_rls
app.dependency_overrides[require_admin] = override_require_admin

client = TestClient(app)

def test_create_agent():
    response = client.post("/v1/admin/agents", json={
        "agent_id": "test-agent-1",
        "name": "Test Agent"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Agent created"
    assert "api_key" in data
    assert data["agent_id"] == "test-agent-1"

@patch("routers.admin.suspend_agent")
def test_suspend_agent(mock_suspend):
    response = client.patch("/v1/admin/agents/test-agent-1/status", json={
        "status": "suspended"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Agent test-agent-1 status updated to suspended"
    mock_suspend.assert_called_once_with("test-agent-1")

@patch("routers.admin.unsuspend_agent")
def test_unsuspend_agent(mock_unsuspend):
    response = client.patch("/v1/admin/agents/test-agent-1/status", json={
        "status": "active"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Agent test-agent-1 status updated to active"
    mock_unsuspend.assert_called_once_with("test-agent-1")

@pytest.mark.asyncio
@patch("routers.proxy.httpx.AsyncClient.send")
def test_stream_proxy(mock_send):
    # Mock the proxy response for OpenAI streaming
    # Using a sync test client for an async streaming response is complex,
    # but we can test if it hits the rate limiter or auth blocks first.
    # To fully test the stream we would need httpx.AsyncClient for the test client.
    
    # We will just test that without API key it fails 401
    response = client.post("/v1/proxy/completions", json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    
    # Because we didn't override require_api_key in this file
    assert response.status_code == 401
