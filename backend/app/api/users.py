from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..schemas import UserCreate, UserOut
from ..crud import create_user, get_user_by_username
from ..auth import get_current_user, require_role
from .deps import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    created = create_user(db, user)
    return created


@router.get("/me", response_model=UserOut)
def read_me(current_user=Depends(get_current_user)):
    return current_user


@router.get('/admin-only')
def admin_only(current_user=Depends(require_role('admin'))):
    return {"msg": "Hello admin", "user": current_user.username}
