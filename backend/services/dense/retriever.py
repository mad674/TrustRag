from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.vector_store import get_qdrant_client
from services.embedding_service.service import get_service as get_embedding_service


class DenseRetriever:
    """Embed a query and retrieve semantically similar evidence from Qdrant."""

    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name

    def retrieve(self, query: str, limit: int = 50, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        vector = get_embedding_service().embed_texts([query])[0]
        hits = get_qdrant_client().search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
        )
        results: List[Dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            if owner_id and payload.get("owner_id") != owner_id:
                continue
            score = float(hit.score)
            results.append({
                "doc_id": payload.get("doc_id"),
                "owner_id": payload.get("owner_id"),
                "title": payload.get("title"),
                "filename": payload.get("filename"),
                "chunk_index": payload.get("chunk_index"),
                "text": payload.get("text"),
                "score": score,
                "similarity_score": score,
                "dense_score": score,
                "bm25_score": 0.0,
                "retrieval_method": "dense",
            })
        return results
