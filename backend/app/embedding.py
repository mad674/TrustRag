from typing import List
import hashlib
import os
import re
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

_embedder = None
VECTOR_SIZE = 384

def get_embedder(model_name: str = "all-MiniLM-L6-v2"):
    global _embedder
    if os.getenv("USE_SENTENCE_TRANSFORMERS", "false").lower() != "true":
        return None
    if _embedder is None:
        if SentenceTransformer is None:
            _embedder = None
        else:
            _embedder = SentenceTransformer(model_name)
    return _embedder


def _hashed_bow_embedding(text: str) -> List[float]:
    """Offline fallback embedding based on normalized token hashing."""
    vector = np.zeros(VECTOR_SIZE, dtype=np.float32)
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    if not tokens:
        return vector.tolist()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_SIZE
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedder()
    if model is None:
        return [_hashed_bow_embedding(t) for t in texts]
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
