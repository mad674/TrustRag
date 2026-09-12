from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import settings
from app.resilience import CircuitBreaker

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class LLMService:
    """Provider adapter with an explicit deterministic local development fallback."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.client = None
        self.circuit = CircuitBreaker(
            "llm-provider",
            failure_threshold=settings.LLM_CIRCUIT_FAILURE_THRESHOLD,
            recovery_timeout=settings.LLM_CIRCUIT_RECOVERY_SECONDS,
        )
        if self.provider in {"openai", "openai-compatible", "gemini"} and settings.OPENAI_API_KEY and OpenAI:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.LLM_BASE_URL or None)

    @property
    def is_external(self) -> bool:
        return self.client is not None

    @property
    def status(self) -> str:
        return f"{self.provider}:external" if self.is_external else "fallback:local"

    def generate(self, system: str, user: str, fallback: str, config: Optional[Dict[str, Any]] = None) -> str:
        active = config or {
            "provider": self.provider,
            "model": self.model,
            "base_url": settings.LLM_BASE_URL,
            "api_key": settings.OPENAI_API_KEY,
            "temperature": settings.LLM_TEMPERATURE,
        }
        provider = str(active.get("provider", "fallback")).lower()
        api_key = active.get("api_key")
        if provider == "fallback" or not api_key or OpenAI is None:
            return fallback
        self.circuit.before_call()
        try:
            client = OpenAI(api_key=api_key, base_url=active.get("base_url") or None, timeout=30.0, max_retries=0)
            response = client.chat.completions.create(
                model=active.get("model", self.model),
                temperature=float(active.get("temperature", settings.LLM_TEMPERATURE)),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception:
            self.circuit.record_failure()
            raise
        self.circuit.record_success()
        content = response.choices[0].message.content
        return content.strip() if content else fallback


_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _service
    if _service is None:
        _service = LLMService()
    return _service
