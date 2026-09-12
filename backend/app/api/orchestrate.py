"""
Orchestrator API endpoint - full end-to-end RAG pipeline
"""
from fastapi import APIRouter, Depends, HTTPException
import re
import uuid
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from ..auth import get_current_user
from services.langgraph.orchestrator import get_orchestrator
from services.langgraph.state import QueryState
from app.resilience import CircuitOpenError
from services.rag_pipeline import get_pipeline
from app.config import settings
from services.llm_service import get_llm_service
from ..api.deps import get_db
from .llm_settings import resolve_user_llm_config
from services.memory_service import UserMemoryService
from ..models_document import Document

router = APIRouter(prefix="/orchestrate", tags=["orchestration"])


class OrchestrateRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)
    document_ids: List[uuid.UUID] = Field(default_factory=list)


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
    pipeline_trace: List[dict]
    llm_provider: str
    task: Optional[str]
    claims: List[dict]
    correction_performed: bool
    reranking_explanation: str
    report: str


@router.post("/query", response_model=OrchestrateResponse)
async def orchestrate_query(
    req: OrchestrateRequest,
    db: Session = Depends(get_db),
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
        user_llm_config = resolve_user_llm_config(db, current_user.id)
        target_docs = []
        if req.document_ids:
            target_docs = db.query(Document).filter(Document.id.in_(req.document_ids), Document.uploaded_by == current_user.id).all()
        else:
            query_terms = {term for term in re.findall(r"[a-z0-9]+", req.query.lower()) if len(term) > 2 and term not in {"summarize", "summary", "this", "document", "paper", "report", "open"}}
            if query_terms:
                candidates = db.query(Document).filter(Document.uploaded_by == current_user.id).all()
                target_docs = [doc for doc in candidates if query_terms & set(re.findall(r"[a-z0-9]+", f"{doc.title} {doc.filename}".lower()))]

        if target_docs and any(word in req.query.lower() for word in ("summarize", "summary", "summarise")):
            chunks = []
            for doc in target_docs:
                normalized = re.sub(r"\s+", " ", doc.content or "").strip()
                for index in range(0, len(normalized), 1200):
                    text = normalized[index:index + 1200].strip()
                    if text:
                        chunks.append({"doc_id": str(doc.id), "owner_id": str(current_user.id), "title": doc.title, "filename": doc.filename, "chunk_index": index // 1200, "text": text, "score": 1.0, "similarity_score": 1.0, "retrieval_strategy": "document_targeted"})
            pipeline_response = {"mode": "adaptive", "phase": "document_targeted", "intent": "summarization", "strategy": "document_targeted", "retrieval_strategy": "document_targeted", "reranker_used": False, "supporting_chunks": chunks, "reranking_explanation": "Document title/filename matched the user query; all matching chunks were passed to the summary agent."}
        else:
            pipeline_response = get_pipeline().run(req.query, top_k=req.top_k, mode="adaptive", owner_id=str(current_user.id))
        retrieved_docs = pipeline_response.get("supporting_chunks", [])
        
        # Step 2: Initialize orchestrator with retrieved documents
        orchestrator = get_orchestrator()
        state: QueryState = {
            "query": req.query,
            "intent": pipeline_response.get("intent"),
            "retrieved_docs": retrieved_docs,
            "structured_answer": None,
            "sources": [],
            "confidence": 0.0,
            "explanations": [],
            "verification_results": None,
            "report": None,
            "task": None,
            "claims": [],
            "refinement_iterations": 0,
            "correction_performed": False,
            "llm_provider": f"{user_llm_config['provider']}:validated",
            "metadata": {
                "user_id": current_user.id,
                "mode": pipeline_response.get("mode"),
                "phase": pipeline_response.get("phase"),
                "retrieval_strategy": pipeline_response.get("retrieval_strategy"),
                "reranker_used": pipeline_response.get("reranker_used"),
                "llm_config": user_llm_config,
                "memory": UserMemoryService().get(db, current_user.id),
            }
        }
        
        # Step 3: Run orchestrator pipeline
        final_state = await orchestrator.process_async(state)
        
        verification = final_state.get("verification_results") or {}
        pipeline_trace = [
            {"stage": "query_analysis", "status": "completed", "detail": f"Intent: {final_state.get('intent', 'qa')}"},
            {"stage": "adaptive_retrieval", "status": "completed", "detail": f"Strategy: {final_state.get('metadata', {}).get('retrieval_strategy', 'unknown')}"},
            {"stage": "cross_encoder_reranking", "status": "completed", "detail": "Applied" if final_state.get('metadata', {}).get('reranker_used') else "Not selected"},
            {"stage": "langgraph_agents", "status": "completed", "detail": f"Task: {final_state.get('task', 'qa')}"},
            {"stage": "claim_extraction", "status": "completed", "detail": f"Extracted {len(final_state.get('claims', []))} claim(s)"},
            {"stage": "evidence_verification", "status": "completed", "detail": verification.get("verification_status", "UNSUPPORTED")},
            {"stage": "correction_search", "status": "completed" if final_state.get("correction_performed") else "skipped", "detail": "One bounded retry performed" if final_state.get("correction_performed") else "Evidence passed without retry"},
            {"stage": "explainability", "status": "completed", "detail": f"{len(final_state.get('sources', []))} citation(s) attached"},
        ]

        # Step 4: Return structured response
        response = OrchestrateResponse(
            query=final_state["query"],
            mode=pipeline_response.get("mode", "adaptive"),
            phase=pipeline_response.get("phase"),
            intent=pipeline_response.get("intent"),
            retrieval_strategy=pipeline_response.get("retrieval_strategy"),
            reranker_used=bool(pipeline_response.get("reranker_used")),
            answer=str(final_state.get("structured_answer") or "The LangGraph agents did not produce an answer."),
            sources=final_state.get("sources", []),
            supporting_chunks=final_state.get("retrieved_docs", []),
            confidence=final_state.get("confidence", 0.0),
            explanations=final_state.get("explanations", []),
            verification=final_state.get("verification_results"),
            pipeline_trace=pipeline_trace,
            llm_provider=final_state.get("llm_provider", get_llm_service().status),
            task=final_state.get("task"),
            claims=final_state.get("claims", []),
            correction_performed=bool(final_state.get("correction_performed")),
            reranking_explanation=pipeline_response.get("reranking_explanation", ""),
            report=final_state.get("report", "")
        )
        UserMemoryService().remember_query(db, current_user.id, req.query, response.model_dump())
        return response
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail="The configured AI provider is temporarily unavailable. Please retry shortly.") from exc
