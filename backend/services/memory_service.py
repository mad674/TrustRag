from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models_memory import QueryRecord, UserMemory


class UserMemoryService:
    """Isolated short-term context and durable research memory per user."""

    def get(self, db: Session, user_id) -> dict[str, list]:
        item = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
        if not item:
            item = UserMemory(user_id=user_id, short_term=[], long_term=[])
            db.add(item)
            db.commit()
            db.refresh(item)
        return {"short_term": item.short_term or [], "long_term": item.long_term or []}

    def remember_query(self, db: Session, user_id, query: str, response: dict) -> None:
        item = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
        if not item:
            item = UserMemory(user_id=user_id, short_term=[], long_term=[])
            db.add(item)
        short_term = list(item.short_term or [])
        short_term.append({"query": query, "intent": response.get("intent"), "strategy": response.get("retrieval_strategy"), "at": datetime.utcnow().isoformat()})
        item.short_term = short_term[-8:]
        long_term = list(item.long_term or [])
        signature = {"intent": response.get("intent"), "strategy": response.get("retrieval_strategy")}
        if signature not in long_term:
            long_term.append(signature)
        item.long_term = long_term[-20:]
        db.add(QueryRecord(
            user_id=user_id,
            query=query,
            intent=response.get("intent"),
            strategy=response.get("retrieval_strategy"),
            confidence=float(response.get("confidence", 0.0)),
            verification_status=(response.get("verification") or {}).get("verification_status"),
            response_json={
                "answer": response.get("answer", ""),
                "sources": response.get("sources", []),
                "supporting_chunks": response.get("supporting_chunks", []),
                "claims": response.get("claims", []),
                "verification": response.get("verification"),
                "explanations": response.get("explanations", []),
                "pipeline_trace": response.get("pipeline_trace", []),
                "report": response.get("report", ""),
                "tool_calls": response.get("tool_calls", []),
                "agent_decisions": response.get("agent_decisions", []),
                "task": response.get("task"),
                "llm_provider": response.get("llm_provider"),
                "reranking_explanation": response.get("reranking_explanation", ""),
                "correction_performed": response.get("correction_performed", False),
            },
        ))
        db.commit()

    def history(self, db: Session, user_id, limit: int = 30) -> list[dict[str, Any]]:
        records = db.query(QueryRecord).filter(QueryRecord.user_id == user_id).order_by(QueryRecord.created_at.desc()).limit(limit).all()
        return [{"id": str(item.id), "query": item.query, "intent": item.intent, "strategy": item.strategy, "confidence": item.confidence, "verification_status": item.verification_status, "created_at": item.created_at.isoformat()} for item in records]

    def get_record(self, db: Session, user_id, record_id) -> dict[str, Any] | None:
        item = db.query(QueryRecord).filter(QueryRecord.id == record_id, QueryRecord.user_id == user_id).first()
        if not item:
            return None
        return {
            "id": str(item.id),
            "query": item.query,
            "intent": item.intent,
            "strategy": item.strategy,
            "confidence": item.confidence,
            "verification_status": item.verification_status,
            "created_at": item.created_at.isoformat(),
            "response": item.response_json or {},
        }
