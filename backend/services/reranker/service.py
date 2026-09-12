from __future__ import annotations

import os
from typing import Any, Dict, List

import numpy as np

from app.embedding import embed_texts

class CrossEncoderReranker:
    """Bounded candidate reranker with an explicit offline similarity fallback."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        enabled = os.getenv("USE_CROSS_ENCODER", "false").lower() == "true"
        self.model = None
        if enabled:
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(model_name)
            except Exception:
                self.model = None

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []
        texts = [candidate.get("text", "") for candidate in candidates]
        if self.model is not None:
            scores = self.model.predict([[query, text] for text in texts])
        else:
            vectors = np.asarray(embed_texts([query, *texts]))
            query_vector = vectors[0]
            document_vectors = vectors[1:]
            denominator = np.linalg.norm(document_vectors, axis=1) * (np.linalg.norm(query_vector) + 1e-12)
            scores = (document_vectors @ query_vector) / np.where(denominator == 0, 1e-12, denominator)
        ranked = []
        for candidate, score in zip(candidates, scores):
            item = candidate.copy()
            item["rerank_score"] = float(score)
            item["score"] = float(score)
            item["rerank_explanation"] = (
                "Cross-Encoder relevance score based on query/evidence interaction"
                if self.model is not None
                else "Local semantic fallback score based on normalized query/evidence embedding similarity"
            )
            ranked.append(item)
        return sorted(ranked, key=lambda item: item["rerank_score"], reverse=True)[:top_k]
