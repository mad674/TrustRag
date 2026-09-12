from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models_document  # noqa: F401 - registers document tables with Base metadata
from . import models_llm  # noqa: F401 - registers per-user AI settings
from . import models_memory  # noqa: F401 - registers isolated memory and query history
from .api import api_router
from .config import settings
from .db import engine
from .models import Base
from .middleware import RequestProtectionMiddleware

app = FastAPI(title=settings.APP_NAME, version="0.1.0")
app.add_middleware(RequestProtectionMiddleware)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
