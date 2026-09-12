def _auth_headers(client, username, email):
    response = client.post(
        "/api/users/register",
        json={"username": username, "email": email, "password": "strongpass"},
    )
    assert response.status_code == 200, response.text
    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "strongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_document_workflows(client):
    headers = _auth_headers(client, "workflow", "workflow@example.com")
    first = client.post(
        "/api/documents/upload",
        files={"file": ("first.txt", b"First document discusses adaptive retrieval and BM25.", "text/plain")},
        headers=headers,
    )
    second = client.post(
        "/api/documents/upload",
        files={"file": ("second.txt", b"Second document discusses dense retrieval and reranking.", "text/plain")},
        headers=headers,
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_id = first.json()["id"]
    second_id = second.json()["id"]

    targeted = client.post(
        "/api/orchestrate/query",
        json={"query": "summary this first document", "top_k": 3},
        headers=headers,
    )
    assert targeted.status_code == 200, targeted.text
    assert targeted.json()["phase"] == "document_targeted"
    assert targeted.json()["task"] == "summary"
    assert targeted.json()["answer"]

    detail = client.get(f"/api/documents/{first_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["processing_status"] == "indexed"

    search = client.get("/api/documents?search=first", headers=headers)
    assert search.status_code == 200
    assert len(search.json()) == 1

    summary = client.post(f"/api/documents/{first_id}/summarize?mode=short", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["summary"]

    comparison = client.post(
        "/api/documents/compare?query=Compare%20retrieval",
        json=[first_id, second_id],
        headers=headers,
    )
    assert comparison.status_code == 200
    assert comparison.json()["answer"]

    report = client.post("/api/reports/generate", json={"query": "retrieval", "top_k": 3}, headers=headers)
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("application/pdf")
    assert report.content.startswith(b"%PDF")

    history = client.get("/api/memory/history", headers=headers)
    assert history.status_code == 200

    deleted = client.delete(f"/api/documents/{first_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get(f"/api/documents/{first_id}", headers=headers).status_code == 404
