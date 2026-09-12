from qdrant_client import QdrantClient
from qdrant_client.http import models
from .config import settings

_client = None


class RemoteQdrantClient:
    def __init__(self, client: QdrantClient):
        self.client = client

    def _ensure_collection(self, collection_name: str, vector_size: int = 384):
        collections = self.client.get_collections().collections
        if not any(item.name == collection_name for item in collections):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    def upsert(self, collection_name: str, points: list[dict]):
        self._ensure_collection(collection_name)
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(id=point["id"], vector=point["vector"], payload=point.get("payload", {}))
                for point in points
            ],
        )

    def search(self, collection_name: str, query_vector: list[float], limit: int = 5):
        self._ensure_collection(collection_name, len(query_vector))
        return self.client.search(collection_name=collection_name, query_vector=query_vector, limit=limit)

    def delete_document(self, collection_name: str, doc_id: str):
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=str(doc_id)))]
                )
            ),
        )


def get_qdrant_client():
    global _client
    if _client is None:
        try:
            remote = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=2)
            remote.get_collections()
            _client = RemoteQdrantClient(remote)
        except Exception:
            from .vector_store import LocalQdrantClient
            _client = LocalQdrantClient()
    return _client
