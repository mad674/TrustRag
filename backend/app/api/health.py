import os
import sqlite3

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..api.deps import get_db
from ..config import settings
from ..models_document import Document
from services.llm_service import get_llm_service

router = APIRouter()

@router.get("/health", tags=["health"])
async def health():
    return {"status":"ok"}

@router.get("/health/readiness", tags=["health"])
def readiness(db: Session = Depends(get_db)):
    """Return actionable subsystem readiness for operators and the dashboard."""
    database = "ok"
    document_count = 0
    try:
        document_count = db.query(Document).count()
    except Exception:
        database = "error"

    vector_store = "ok"
    vector_count = 0
    try:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "vector_store.sqlite3"))
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            try:
                vector_count = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
            finally:
                conn.close()
        else:
            vector_store = "not_initialized"
    except Exception:
        vector_store = "error"

    llm = get_llm_service()
    status = "ok" if database == "ok" and vector_store in {"ok", "not_initialized"} else "degraded"
    return {
        "status": status,
        "app": settings.APP_NAME,
        "database": {"status": database, "documents": document_count},
        "vector_store": {"status": vector_store, "vectors": vector_count},
        "llm": {"status": llm.status, "provider": llm.provider},
    }
