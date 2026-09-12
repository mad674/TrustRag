from fastapi.testclient import TestClient


def test_register_and_login(client: TestClient):
    payload = {"username": "alice", "email": "alice@example.com", "password": "strongpass"}

    response = client.post("/api/users/register", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"

    token_response = client.post(
        "/api/auth/token",
        data={"username": "alice", "password": "strongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_response.status_code == 200, token_response.text
    body = token_response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_auth_me_requires_token(client: TestClient):
    response = client.get("/api/users/me")
    assert response.status_code == 401
