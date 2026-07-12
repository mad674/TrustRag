from fastapi import APIRouter
from pydantic import BaseModel
from services.adaptive_retrieval.service import get_service as get_adaptive_service
from services.rag_pipeline import get_pipeline

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


class QueryIn(BaseModel):
    query: str
    top_k: int = 5


@router.post('/query')
def query(q: QueryIn):
    svc = get_adaptive_service()
    return svc.query(q.query, top_k=q.top_k)


@router.post('/rag')
def adaptive_rag(q: QueryIn):
    return get_pipeline().run(q.query, top_k=q.top_k, mode="adaptive")
