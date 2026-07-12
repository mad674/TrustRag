from fastapi import APIRouter

api_router = APIRouter()

from . import health, users, auth
from . import documents
from . import embeddings, retrieve
from . import adaptive, orchestrate, evaluation

api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(embeddings.router)
api_router.include_router(retrieve.router)
api_router.include_router(adaptive.router)
api_router.include_router(orchestrate.router)
api_router.include_router(evaluation.router)
