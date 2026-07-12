from typing import List, Dict
import os
try:
    from sentence_transformers import CrossEncoder
except Exception:
    CrossEncoder = None

from app.embedding import embed_texts
import numpy as np

class Reranker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model_name = model_name
        use_cross_encoder = os.getenv("USE_CROSS_ENCODER", "false").lower() == "true"
        self.model = CrossEncoder(model_name) if use_cross_encoder and CrossEncoder is not None else None

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        # candidates: list of {doc_id, chunk_index, text, payload?}
        if not candidates:
            return []
        texts = [c['text'] for c in candidates]
        if self.model is not None:
            pairs = [[query, t] for t in texts]
            scores = self.model.predict(pairs)
            scored = []
            for c, s in zip(candidates, scores):
                cc = c.copy()
                cc['score'] = float(s)
                scored.append(cc)
            scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)[:top_k]
            return scored_sorted
        else:
            # fallback: use embedding cosine similarity
            vecs = embed_texts([query] + texts)
            qv = np.array(vecs[0])
            cvs = np.array(vecs[1:])
            denom = np.linalg.norm(cvs, axis=1) * (np.linalg.norm(qv) + 1e-12)
            sims = (cvs @ qv) / np.where(denom == 0, 1e-12, denom)
            scored = []
            for c, s in zip(candidates, sims):
                cc = c.copy()
                cc['score'] = float(s)
                scored.append(cc)
            scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)[:top_k]
            return scored_sorted
