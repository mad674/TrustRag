from services.document_ingestion.chunking import chunk_text
from services.document_ingestion.parsers import extract_text
from services.hybrid.retriever import HybridRetriever
from services.langgraph.orchestrator import TrustRAGOrchestrator


def test_ingestion_services_parse_and_chunk():
    parsed = extract_text("notes.txt", b"First sentence. Second sentence about retrieval.")
    chunks = chunk_text(parsed["text"], max_chars=30, overlap=5)
    assert parsed["text"].startswith("First sentence")
    assert chunks
    assert all(item["text"] for item in chunks)
    assert all("chunk_index" in item for item in chunks)


def test_hybrid_service_fuses_ranked_candidates():
    lexical = [{"doc_id": "a", "chunk_index": 0, "text": "exact term", "score": 4.0}]
    dense = [{"doc_id": "b", "chunk_index": 0, "text": "semantic term", "score": 0.9}]
    results = HybridRetriever().retrieve(lexical, dense, top_k=2)
    assert len(results) == 2
    assert {item["retrieval_method"] for item in results} == {"hybrid_rrf"}
    assert all("score" in item for item in results)


def test_langgraph_orchestrator_has_bounded_compiled_graph():
    orchestrator = TrustRAGOrchestrator()
    state = {
        "query": "What is retrieval?",
        "intent": "qa",
        "retrieved_docs": [{"doc_id": "doc-1", "title": "Notes", "text": "Retrieval finds relevant evidence.", "score": 1.0}],
        "structured_answer": None,
        "sources": [],
        "confidence": 0.0,
        "explanations": [],
        "verification_results": None,
        "report": None,
        "metadata": {"retrieval_strategy": "dense", "reranker_used": False},
    }
    result = orchestrator.process(state)
    assert result["structured_answer"]
    assert result["sources"]
    assert result["report"]
