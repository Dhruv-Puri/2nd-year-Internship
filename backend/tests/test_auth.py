# tests/test_auth.py
from fastapi.testclient import TestClient
from backend.app.main import app  # Adjust this import path based on how you run it

client = TestClient(app)

def test_login_invalid_credentials():
    """
    Test that the API correctly rejects invalid login attempts 
    and returns a 401 Unauthorized status.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent_user@lpu.edu.in", "password": "wrongpassword123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_register_missing_fields():
    """
    Test that Pydantic correctly intercepts and rejects malformed 
    registration payloads before they hit the database.
    """
    response = client.post(
        "/api/auth/register",
        json={"email": "test@lpu.edu.in"} # Missing password and name
    )
    assert response.status_code == 422 # Unprocessable Entity
