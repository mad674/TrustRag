from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..vector_store import get_qdrant_client
from ..embedding import embed_texts
from services.rag_pipeline import get_pipeline

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


class QueryIn(BaseModel):
    query: str
    top_k: int = 5


@router.post('/vector')
def retrieve_vector(q: QueryIn):
    vectors = embed_texts([q.query])
    if not vectors:
        raise HTTPException(status_code=400, detail='Embedding failed')
    vec = vectors[0]
    qc = get_qdrant_client()
    hits = qc.search(collection_name='documents', query_vector=vec, limit=q.top_k)
    results = []
    for h in hits:
        results.append({
            'id': h.id,
            'score': h.score,
            'payload': h.payload,
        })
    return {'results': results}


@router.post('/baseline')
def baseline_rag(q: QueryIn):
    return get_pipeline().run(q.query, top_k=q.top_k, mode="baseline")
