from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import api_router
from .models import Base
from . import models_document  # noqa: F401 - registers document tables with Base metadata
from .db import engine

app = FastAPI(title="TrustRAG Backend")

# CORS - allow frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],#"http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    # ensure DB tables exist for quick dev
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health():
    return {"status": "ok"}
