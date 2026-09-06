from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_login_success():
    response = client.post("/auth/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_unauthorized_chat():
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 403 or response.status_code == 401