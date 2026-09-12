# API Overview

## Authentication

- POST /api/auth/token
- POST /api/users/register
- GET /api/users/me

## Document management

- POST /api/documents/upload
- GET /api/documents
- GET /api/documents/{id}
- DELETE /api/documents/{id}

## Query and retrieval

- POST /api/query
- POST /api/query/stream
- POST /api/retrieve/vector
- POST /api/adaptive/query
- POST /api/orchestrate/query

## Evaluation

- POST /api/evaluation/compare
- GET /api/evaluation/results

## Health and operational status

- GET /health
- GET /api/health

## OpenAPI

FastAPI automatically exposes the interactive documentation at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Notes

The API currently contains a functional prototype layer and is being expanded toward the full academic feature set and user isolation model required by the final project specification.
