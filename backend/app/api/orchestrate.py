"""
Orchestrator API endpoint - full end-to-end RAG pipeline
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..auth import get_current_user
from services.langgraph.orchestrator import get_orchestrator
from services.langgraph.state import QueryState
from services.rag_pipeline import get_pipeline

router = APIRouter(prefix="/orchestrate", tags=["orchestration"])


class OrchestrateRequest(BaseModel):
    query: str
    top_k: int = 10


class OrchestrateResponse(BaseModel):
    query: str
    mode: str
    phase: Optional[str]
    intent: Optional[str]
    retrieval_strategy: Optional[str]
    reranker_used: bool
    answer: str
    sources: List[dict]
    supporting_chunks: List[dict]
    confidence: float
    explanations: List[str]
    verification: Optional[dict]
    report: str


@router.post("/query", response_model=OrchestrateResponse)
async def orchestrate_query(
    req: OrchestrateRequest,
    current_user = Depends(get_current_user)
):
    """
    Full end-to-end RAG orchestration:
    1. Adaptive retrieval
    2. Multi-agent answer generation
    3. Verification & grounding
    4. Report generation
    """
    try:
        pipeline_response = get_pipeline().run(req.query, top_k=req.top_k, mode="adaptive")
        retrieved_docs = pipeline_response.get("supporting_chunks", [])
        
        # Step 2: Initialize orchestrator with retrieved documents
        orchestrator = get_orchestrator()
        state: QueryState = {
            "query": req.query,
            "intent": pipeline_response.get("intent"),
            "retrieved_docs": retrieved_docs,
            "structured_answer": pipeline_response.get("answer"),
            "sources": pipeline_response.get("sources", []),
            "confidence": pipeline_response.get("confidence", 0.0),
            "explanations": pipeline_response.get("explanations", []),
            "verification_results": pipeline_response.get("verification"),
            "report": pipeline_response.get("report"),
            "metadata": {
                "user_id": current_user.id,
                "mode": pipeline_response.get("mode"),
                "phase": pipeline_response.get("phase"),
                "retrieval_strategy": pipeline_response.get("retrieval_strategy"),
                "reranker_used": pipeline_response.get("reranker_used"),
            }
        }
        
        # Step 3: Run orchestrator pipeline
        final_state = await orchestrator.process_async(state)
        
        # Step 4: Return structured response
        return OrchestrateResponse(
            query=final_state["query"],
            mode=pipeline_response.get("mode", "adaptive"),
            phase=pipeline_response.get("phase"),
            intent=pipeline_response.get("intent"),
            retrieval_strategy=pipeline_response.get("retrieval_strategy"),
            reranker_used=bool(pipeline_response.get("reranker_used")),
            answer=final_state.get("structured_answer", ""),
            sources=final_state.get("sources", []),
            supporting_chunks=pipeline_response.get("supporting_chunks", []),
            confidence=final_state.get("confidence", 0.0),
            explanations=final_state.get("explanations", []),
            verification=final_state.get("verification_results"),
            report=final_state.get("report", "")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
