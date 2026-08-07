from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()

def test_tasks_require_authorization():
    response = client.get("/tasks")

    assert response.status_code == 401