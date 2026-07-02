import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import get_db

# Override the database dependency so it doesn't try to connect to a real DB
async def override_get_db():
    class MockSession:
        async def execute(self, *args, **kwargs):
            return True
    yield MockSession()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthorized_access():
    response = client.get("/v1/agents/metrics")
    assert response.status_code == 401
