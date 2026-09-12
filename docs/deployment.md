# Deployment Guide

## Docker deployment

```bash
docker compose up --build
```

This is the recommended local deployment path for the project. It includes the frontend, backend, Postgres, and Qdrant services.

## Environment configuration

Use a project-root `.env` file created from `.env.example` and configure:

- DATABASE_URL
- QDRANT_URL
- JWT_SECRET
- LLM_PROVIDER
- OPENAI_API_KEY
- GEMINI_API_KEY
- EMBEDDING_MODEL
- RERANKER_MODEL
- CORS_ORIGINS

## Production notes

- Keep secrets in a secure environment manager.
- Do not expose internal prompts or API keys in client-facing responses.
- Use strict CORS settings in production.
- Use HTTPS and a reverse proxy in production deployments.

## Observability

Log request IDs, user IDs, document IDs, retrieval strategy, verification outcomes, and latency. Avoid logging secrets or documents unnecessarily.
