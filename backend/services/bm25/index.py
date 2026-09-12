from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.adaptive_retrieval.bm25_index import BM25Index


class BM25Retriever:
    """Public BM25 retrieval service with owner filtering."""

    def __init__(self):
        self.index = BM25Index()

    def build(self, chunks: List[Dict[str, Any]]) -> None:
        self.index.build(chunks)

    def retrieve(self, query: str, top_k: int = 10, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.index.query(query, top_k=top_k)
        if owner_id:
            results = [item for item in results if item.get("owner_id") in {owner_id, None}]
        return results
