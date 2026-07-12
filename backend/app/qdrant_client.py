from qdrant_client import QdrantClient
from .config import settings

_client = None

def get_qdrant_client():
    global _client
    if _client is None:
        url = settings.QDRANT_URL
        # QdrantClient accepts host and port when using HTTP
        if url.startswith('http'):
            # simple parse
            host = url.replace('http://', '').replace('https://', '').split(':')[0]
            port = int(url.split(':')[-1]) if ':' in url else 6333
            _client = QdrantClient(host=host, port=port)
        else:
            _client = QdrantClient(url)
    return _client
