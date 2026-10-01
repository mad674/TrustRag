import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..api.deps import get_db
from ..models_document import Document
from ..auth import get_current_user
from .documents import index_document_content

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post('/index/{doc_id}')
def index_document(doc_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.uploaded_by == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')
    doc.processing_status = "processing"
    db.commit()
    try:
        indexed_chunks = index_document_content(doc)
        doc.processing_status = "indexed"
        db.commit()
    except Exception as exc:
        doc.processing_status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Evidence indexing failed. Check the embedding/vector service and retry.") from exc
    if not indexed_chunks:
        raise HTTPException(status_code=400, detail='No text to embed')
    return {"indexed_chunks": indexed_chunks}
