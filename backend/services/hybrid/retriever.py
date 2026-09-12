from __future__ import annotations

from typing import Any, Dict, List, Tuple


class HybridRetriever:
    """Fuse lexical and dense candidates using reciprocal rank fusion."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def retrieve(
        self,
        bm25_results: List[Dict[str, Any]],
        dense_results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        candidates: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
        fused_scores: Dict[Tuple[Any, Any], float] = {}
        for rank, result in enumerate(bm25_results, start=1):
            key = (result.get("doc_id"), result.get("chunk_index"))
            candidates.setdefault(key, result.copy())
            candidates[key]["bm25_score"] = max(float(candidates[key].get("bm25_score", 0.0)), float(result.get("score", 0.0)))
            fused_scores[key] = fused_scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)
        for rank, result in enumerate(dense_results, start=1):
            key = (result.get("doc_id"), result.get("chunk_index"))
            candidates.setdefault(key, result.copy())
            candidates[key]["dense_score"] = max(float(candidates[key].get("dense_score", 0.0)), float(result.get("score", 0.0)))
            candidates[key]["text"] = candidates[key].get("text") or result.get("text")
            candidates[key]["title"] = candidates[key].get("title") or result.get("title")
            fused_scores[key] = fused_scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)

        results = []
        for key, item in candidates.items():
            item["score"] = fused_scores[key]
            item["similarity_score"] = fused_scores[key]
            item["retrieval_method"] = "hybrid_rrf"
            results.append(item)
        return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
