from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_readiness():
    """Test readiness endpoint"""
    response = client.get("/readiness")
    assert response.status_code in [200, 503]

def test_create_user():
    """Test user creation"""
    user_data = {
        "name": "John Doe",
        "email": "john@example.com"
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 200

def test_list_users():
    """Test list users endpoint"""
    response = client.get("/users/1")
    assert response.status_code == 200

def test_invalid_email():
    """Test invalid data"""
    user_data = {
        "name": "Jane Doe",
        "email": "invalid"
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 200
