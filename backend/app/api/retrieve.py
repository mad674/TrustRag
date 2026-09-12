from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..auth import get_current_user
from ..vector_store import get_qdrant_client
from services.rag_pipeline import get_pipeline
from services.adaptive_retrieval.service import get_service as get_adaptive_service

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


class QueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)


@router.post('/vector')
def retrieve_vector(q: QueryIn, current_user=Depends(get_current_user)):
    if not q.query.strip():
        raise HTTPException(status_code=422, detail='Query must not be empty')
    response = get_adaptive_service().retrieve(
        q.query,
        top_k=q.top_k,
        strategy='dense',
        owner_id=str(current_user.id),
    )
    return response


@router.post('/baseline')
def baseline_rag(q: QueryIn, current_user=Depends(get_current_user)):
    return get_pipeline().run(q.query, top_k=q.top_k, mode="baseline", owner_id=str(current_user.id))


@router.post('/adaptive')
def adaptive_retrieval(q: QueryIn, current_user=Depends(get_current_user)):
    if not q.query.strip():
        raise HTTPException(status_code=422, detail='Query must not be empty')
    return get_adaptive_service().query(q.query, top_k=q.top_k, owner_id=str(current_user.id))
