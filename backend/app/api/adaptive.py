from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..auth import get_current_user
from services.adaptive_retrieval.service import get_service as get_adaptive_service
from services.rag_pipeline import get_pipeline

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


class QueryIn(BaseModel):
    query: str
    top_k: int = 5


@router.post('/query')
def query(q: QueryIn, current_user=Depends(get_current_user)):
    svc = get_adaptive_service()
    return svc.query(q.query, top_k=q.top_k, owner_id=str(current_user.id))


@router.post('/rag')
def adaptive_rag(q: QueryIn, current_user=Depends(get_current_user)):
    return get_pipeline().run(q.query, top_k=q.top_k, mode="adaptive", owner_id=str(current_user.id))
