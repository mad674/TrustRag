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


def test_adaptive_retrieval_is_authenticated_and_owner_scoped(client):
    owner_headers = _auth_headers(client, "researcher", "researcher@example.com")
    other_headers = _auth_headers(client, "visitor", "visitor@example.com")

    upload = client.post(
        "/api/documents/upload",
        files={"file": ("research.txt", b"Adaptive retrieval combines lexical BM25 evidence with dense semantic search.", "text/plain")},
        headers=owner_headers,
    )
    assert upload.status_code == 200, upload.text

    unauthenticated = client.post("/api/retrieve/adaptive", json={"query": "adaptive retrieval"})
    assert unauthenticated.status_code == 401

    owner_result = client.post(
        "/api/retrieve/adaptive",
        json={"query": "adaptive retrieval", "top_k": 3},
        headers=owner_headers,
    )
    assert owner_result.status_code == 200, owner_result.text
    assert owner_result.json()["results"]

    comparison = client.post(
        "/api/evaluation/compare",
        json={"query": "adaptive retrieval", "top_k": 3, "relevant_doc_ids": [upload.json()["id"]]},
        headers=owner_headers,
    )
    assert comparison.status_code == 200, comparison.text
    assert len(comparison.json()["results"]) == 4
    assert all("latency_ms" in row and "confidence" in row for row in comparison.json()["results"])

    orchestration = client.post(
        "/api/orchestrate/query",
        json={"query": "adaptive retrieval", "top_k": 3},
        headers=owner_headers,
    )
    assert orchestration.status_code == 200, orchestration.text
    trace = orchestration.json()["pipeline_trace"]
    stages = [step["stage"] for step in trace]
    assert stages == [
        "query_analysis",
        "adaptive_retrieval",
        "cross_encoder_reranking",
        "langgraph_agents",
        "claim_extraction",
        "evidence_verification",
        "correction_search",
        "explainability",
    ]
    orchestration_body = orchestration.json()
    assert orchestration_body["answer"]
    assert orchestration_body["llm_provider"] == "fallback:validated"
    assert orchestration_body["verification"] is not None
    assert "claims" in orchestration_body["verification"]
    assert orchestration_body["report"]

    summary_query = client.post(
        "/api/orchestrate/query",
        json={"query": "Summarize the adaptive retrieval evidence", "top_k": 3},
        headers=owner_headers,
    )
    assert summary_query.status_code == 200, summary_query.text
    assert isinstance(summary_query.json()["answer"], str)
    assert summary_query.json()["answer"]
    assert summary_query.json()["task"] == "summary"

    other_result = client.post(
        "/api/retrieve/adaptive",
        json={"query": "adaptive retrieval", "top_k": 3},
        headers=other_headers,
    )
    assert other_result.status_code == 200, other_result.text
    owner_id = upload.json()["id"]
    assert other_result.json()["results"] == []
