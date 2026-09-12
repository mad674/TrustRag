from io import BytesIO


def test_document_upload_and_list(client):
    register = client.post(
        "/api/users/register",
        json={"username": "docuser", "email": "docuser@example.com", "password": "strongpass"},
    )
    assert register.status_code == 200, register.text

    login = client.post(
        "/api/auth/token",
        data={"username": "docuser", "password": "strongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = client.post(
        "/api/documents/upload",
        files={"file": ("sample.txt", b"This is a sample document about adaptive retrieval and document verification.", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "sample.txt"
    assert body["filename"] == "sample.txt"

    listings = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert listings.status_code == 200, listings.text
    assert len(listings.json()) >= 1
