from app.llm_security import decrypt_api_key
from app.models_llm import UserLLMSettings


def _headers(client, username, email):
    registered = client.post(
        "/api/users/register",
        json={"username": username, "email": email, "password": "strongpass"},
    )
    assert registered.status_code == 200, registered.text
    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "strongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_user_llm_settings_are_verified_encrypted_and_isolated(client, db_session):
    first_headers = _headers(client, "aiowner", "aiowner@example.com")
    second_headers = _headers(client, "anotherai", "anotherai@example.com")

    saved = client.post(
        "/api/settings/llm/validate",
        json={"provider": "fallback", "model": "local-grounded", "temperature": 0.2, "max_tokens": 800},
        headers=first_headers,
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["is_verified"] is True
    assert saved.json()["has_api_key"] is False

    first = client.get("/api/settings/llm", headers=first_headers)
    second = client.get("/api/settings/llm", headers=second_headers)
    assert first.json()["provider"] == "fallback"
    assert second.json()["provider"] == "fallback"

    external = client.post(
        "/api/settings/llm/validate",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile", "api_key": "invalid-key", "temperature": 0.2, "max_tokens": 800},
        headers=first_headers,
    )
    assert external.status_code == 422
