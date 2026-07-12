from typing import List
import os
from . import cache as _cache
from app.embedding import embed_texts as local_embed
from app.config import settings

try:
    import openai
except Exception:
    openai = None


class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        batch = settings.EMBEDDING_BATCH_SIZE
        self.batch_size = int(batch) if batch else 32
        storage = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
        os.makedirs(storage, exist_ok=True)
        dbpath = os.path.join(storage, 'embeddings_cache.db')
        _cache.init(dbpath)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # check cache
        cached = _cache.get(texts)
        if cached:
            return cached
        # choose provider
        if self.provider == 'openai' and openai is not None and settings.OPENAI_API_KEY:
            vectors = self._openai_batch(texts)
        elif self.provider == 'sentence-transformers':
            vectors = local_embed(texts)
        else:
            # fallback local embed (uses sentence-transformers fallback)
            vectors = local_embed(texts)
        # cache result
        _cache.set_(texts, vectors)
        return vectors

    def _openai_batch(self, texts: List[str]) -> List[List[float]]:
        # use OpenAI embeddings API
        openai.api_key = settings.OPENAI_API_KEY
        vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            resp = openai.Embedding.create(model='text-embedding-3-small', input=batch)
            for e in resp['data']:
                vectors.append(e['embedding'])
        return vectors


# convenience singleton
_service = None

def get_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
