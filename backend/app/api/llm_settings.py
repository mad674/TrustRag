from __future__ import annotations

import datetime
import socket
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy.orm import Session

from ..api.deps import get_db
from ..auth import get_current_user
from ..llm_security import decrypt_api_key, encrypt_api_key
from ..models_llm import UserLLMSettings

router = APIRouter(prefix="/settings/llm", tags=["llm-settings"])


class LLMSettingsRequest(BaseModel):
    provider: str = Field(pattern="^(fallback|openai|groq|openai-compatible)$")
    model: str = Field(min_length=2, max_length=160)
    base_url: Optional[str] = Field(default=None, max_length=500)
    api_key: Optional[SecretStr] = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class LLMSettingsResponse(BaseModel):
    provider: str
    model: str
    base_url: Optional[str]
    temperature: float
    is_verified: bool
    has_api_key: bool
    verified_at: Optional[str]


class LLMKeyResponse(BaseModel):
    has_api_key: bool
    is_verified: bool


def _response(item: UserLLMSettings) -> LLMSettingsResponse:
    return LLMSettingsResponse(
        provider=item.provider,
        model=item.model,
        base_url=item.base_url,
        temperature=item.temperature,
        is_verified=item.is_verified,
        has_api_key=bool(item.encrypted_api_key),
        verified_at=item.verified_at.isoformat() if item.verified_at else None,
    )


def get_user_llm_settings(db: Session, user_id) -> UserLLMSettings:
    item = db.query(UserLLMSettings).filter(UserLLMSettings.user_id == user_id).first()
    if not item:
        item = UserLLMSettings(user_id=user_id, provider="fallback", model="local-grounded", is_verified=True)
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


@router.get("", response_model=LLMSettingsResponse)
def read_llm_settings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _response(get_user_llm_settings(db, current_user.id))


@router.post("/validate", response_model=LLMSettingsResponse)
def validate_llm_settings(request: LLMSettingsRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    api_key = request.api_key.get_secret_value() if request.api_key else None
    if request.provider == "fallback":
        if api_key:
            raise HTTPException(status_code=400, detail="Local fallback does not accept an API key")
        verified = True
    else:
        if not api_key:
            raise HTTPException(status_code=422, detail="An API key is required for an external provider")
        base_url = request.base_url or ("https://api.groq.com/openai/v1" if request.provider == "groq" else None)
        try:
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=12.0, max_retries=0)
            client.models.list()
            verified = True
        except socket.timeout as exc:
            raise HTTPException(status_code=422, detail="Provider validation timed out. Check the endpoint and network connection.") from exc
        except Exception as exc:
            detail = str(exc).strip() or "The provider rejected the key or endpoint."
            raise HTTPException(status_code=422, detail=f"Provider validation failed: {detail}") from exc

    item = get_user_llm_settings(db, current_user.id)
    item.provider = request.provider
    item.model = request.model
    item.base_url = request.base_url or ("https://api.groq.com/openai/v1" if request.provider == "groq" else None)
    item.temperature = request.temperature
    if request.provider == "fallback":
        item.encrypted_api_key = None
    elif api_key:
        item.encrypted_api_key = encrypt_api_key(api_key)
    item.is_verified = verified
    item.verified_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _response(item)


@router.delete("/key", response_model=LLMKeyResponse)
def revoke_llm_key(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Revoke the user's stored provider secret without returning its value."""
    item = get_user_llm_settings(db, current_user.id)
    item.encrypted_api_key = None
    item.is_verified = item.provider == "fallback"
    item.verified_at = datetime.datetime.utcnow() if item.is_verified else None
    db.commit()
    return LLMKeyResponse(has_api_key=False, is_verified=item.is_verified)


def resolve_user_llm_config(db: Session, user_id) -> dict:
    item = get_user_llm_settings(db, user_id)
    if item.provider != "fallback" and (not item.is_verified or not item.encrypted_api_key):
        raise HTTPException(status_code=428, detail="Configure and verify an AI provider, or select the local fallback, before using AI analysis")
    return {
        "provider": item.provider,
        "model": item.model,
        "base_url": item.base_url,
        "api_key": decrypt_api_key(item.encrypted_api_key),
        "temperature": item.temperature,
    }
