from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..api.deps import get_db
from ..models_document import Document
from ..auth import get_current_user
from .documents import index_document_content

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post('/index/{doc_id}')
def index_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or (doc.uploaded_by not in {None, current_user.id}):
        raise HTTPException(status_code=404, detail='Document not found')
    indexed_chunks = index_document_content(doc)
    if not indexed_chunks:
        raise HTTPException(status_code=400, detail='No text to embed')
    return {"indexed_chunks": indexed_chunks}
