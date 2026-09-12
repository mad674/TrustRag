# Setup Guide

## Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Qdrant
- Docker and Docker Compose (optional)

## Local environment

1. Copy the sample environment file:

```bash
cp .env.example .env
```

2. Update the values in `.env` for your local machine.

3. Create and activate a virtual environment:

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

4. Install backend dependencies:

```bash
pip install -r requirements.txt
```

5. Start PostgreSQL and ensure the database exists.

6. Start the backend:

```bash
uvicorn app.main:app --reload
```

7. Start the frontend:

```bash
cd ../frontend
npm install
npm run dev
```

## Docker startup

```bash
docker compose up --build
```

This project is designed to launch the frontend, backend, Postgres, and Qdrant as a complete local stack.

## Health checks

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs
- Qdrant: http://localhost:6333
- Postgres: localhost:5432

## Notes

- The project uses a local development fallback mode when external AI services are unavailable.
- Configuration errors should be surfaced clearly when AI features are requested.
- Do not commit `.env` values to the repository.
