import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..api.deps import get_db
from ..auth import get_current_user
from services.memory_service import UserMemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("")
def read_memory(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return UserMemoryService().get(db, current_user.id)


@router.get("/history")
def read_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return UserMemoryService().history(db, current_user.id)


@router.get("/history/{record_id}")
def read_history_record(record_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    record = UserMemoryService().get_record(db, current_user.id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found")
    return record
