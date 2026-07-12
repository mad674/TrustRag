# Embedding Service

Provides a pluggable embedding service with batching and caching.

Providers supported (configurable via `EMBEDDING_PROVIDER`):
- `openai` - OpenAI embeddings (requires `OPENAI_API_KEY` env var)
- `sentence-transformers` - local sentence-transformers model
- `fallback` - deterministic pseudo-random vectors (for development)

Usage:
- Import `EmbeddingService` from `backend.services.embedding_service.service` and call `embed_texts(texts)` or use `index_document(doc_id)` convenience methods.
