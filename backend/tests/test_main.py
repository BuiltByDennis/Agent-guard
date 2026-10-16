from fastapi.testclient import TestClient

from database import get_db
from main import app


# Override the database dependency so it doesn't try to connect to a real DB
async def override_get_db():
    class MockSession:
        async def execute(self, *args, **kwargs):
            return True

    yield MockSession()


client = TestClient(app)


def test_health_check():
    app.dependency_overrides[get_db] = override_get_db
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"


def test_unauthorized_access():
    response = client.get("/v1/agents/metrics")
    assert response.status_code == 401
