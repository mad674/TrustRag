import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_current_user
from services.rag_pipeline import get_pipeline

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationRequest(BaseModel):
    query: str
    top_k: int = 5
    relevant_doc_ids: Optional[List[uuid.UUID]] = None



def _precision_at_k(sources: List[dict], relevant_doc_ids: List[uuid.UUID]) -> float:
    if not sources or not relevant_doc_ids:
        return 0.0
    relevant_ids = {str(item) for item in relevant_doc_ids}
    hits = sum(1 for source in sources if str(source.get("doc_id")) in relevant_ids)
    return hits / len(sources)


def _recall_at_k(sources: List[dict], relevant_doc_ids: List[uuid.UUID]) -> float:
    if not sources or not relevant_doc_ids:
        return 0.0
    retrieved = {str(source.get("doc_id")) for source in sources}
    hits = len(retrieved & {str(item) for item in relevant_doc_ids})
    return hits / len(relevant_doc_ids)


@router.post("/compare")
def compare_modes(req: EvaluationRequest, current_user=Depends(get_current_user)):
    pipeline = get_pipeline()
    modes = ["baseline", "hybrid", "hybrid_rerank", "adaptive"]
    rows = []
    relevant = req.relevant_doc_ids or []

    for mode in modes:
        started = time.perf_counter()
        result = pipeline.run(req.query, top_k=req.top_k, mode=mode, owner_id=str(current_user.id))
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        verification = result.get("verification", {})
        sources = result.get("sources", [])
        rows.append({
            "mode": mode,
            "intent": result.get("intent"),
            "strategy": result.get("retrieval_strategy"),
            "reranker_used": result.get("reranker_used"),
            "confidence": result.get("confidence"),
            "evidence_score": verification.get("evidence_score"),
            "hallucination_score": verification.get("hallucination_score"),
            "hallucination_risk": verification.get("hallucination_risk"),
            "precision_at_k": _precision_at_k(sources, relevant),
            "recall_at_k": _recall_at_k(sources, relevant),
            "latency_ms": latency_ms,
            "source_count": len(sources),
        })

    return {
        "query": req.query,
        "top_k": req.top_k,
        "relevant_doc_ids": relevant,
        "results": rows,
        "research_claim": (
            "Compare dense baseline, fixed hybrid, hybrid rerank, and TrustRAG adaptive retrieval "
            "to measure retrieval quality, hallucination reduction, confidence, and latency."
        ),
    }
