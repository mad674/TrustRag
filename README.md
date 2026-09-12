# AdaptiveDocAI

Adaptive Explainable Multi-Agent Retrieval-Augmented Framework for Intelligent Document Analysis

## Research project status

This repository is being built as a full academic RAG project for adaptive retrieval and trustworthy document analysis. The codebase already contains a working starter prototype, but the implementation is being evolved in staged phases toward the final research architecture described in the project brief.

The official project title remains:

Adaptive Explainable Multi-Agent Retrieval-Augmented Framework for Intelligent Document Analysis

Internal name:

AdaptiveDocAI

## Core research focus

- Adaptive retrieval selection
- Multi-agent orchestration
- Evidence verification
- Confidence-aware explainability
- Grounded citation generation
- Trustworthy document analysis

This project is not being presented as a generic chatbot with RAG. The research emphasis is on retrieval strategy selection and trustworthy evidence-grounded reasoning.

## Current repository analysis

### Existing work already present

- FastAPI backend shell
- JWT auth and user routes
- basic document upload API
- PLANNED retrieval and evaluation endpoints
- Vite + React frontend shell
- Docker-oriented config files
- sample environment configuration
- partial research-oriented docs and service directories

### Must still be implemented or hardened

- PostgreSQL schema for the full research model set
- strict user isolation across all doc operations
- real chunking with metadata and page tracking
- embedding service using BGE-like configuration
- Qdrant collection lifecycle and document filtering
- BM25 lexical index with safe rebuilds
- dense and hybrid retrieval with principled score fusion
- adaptive router using query features
- reranking and multi-agent LangGraph flow
- verification, contradiction handling, and confidence computation
- dashboard, comparison, summaries, reports, and evaluation pipeline
- reproducible experiments and real metric exports

## Implementation plan

### Phase 1: Foundation

Completed in this update:

- repository assessment and truthful project framing
- environment config alignment for the full academic project
- documentation update across architecture, setup, methodology, evaluation, API, and deployment
- validation of the existing frontend build and Python compile baseline

### Phase 2: Data and authentication

Planned next:

- finalize PostgreSQL models and migrations
- secure JWT auth and role checks
- document metadata model and user isolation rules
- upload and validation contracts

### Phase 3: Retrieval stack

Planned next:

- chunking service with structural/semantic chunk metadata
- embedding service and Qdrant indexing
- BM25 implementation
- dense retrieval
- hybrid fusion and reranking

### Phase 4: Agents and verification

Planned next:

- LangGraph orchestrator and agents
- evidence verification and contradiction detection
- confidence scoring and explainability

### Phase 5: UI and evaluation

Planned next:

- chat, dashboard, comparison, report generation, and evaluation runner
- results export and plotting
- ablation studies and experiment reproducibility

## Project structure

```text
TrustRAG/
├── backend/
│   ├── app/
│   ├── services/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── setup.md
│   ├── research_methodology.md
│   ├── evaluation.md
│   └── deployment.md
├── evaluation/
├── .env.example
├── docker-compose.yml
├── README.md
└── startup.py
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000   
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

## Environment variables

Use the project-root `.env` file derived from `.env.example` and configure values for:

- DATABASE_URL
- QDRANT_URL
- JWT_SECRET
- LLM_PROVIDER
- OPENAI_API_KEY
- GEMINI_API_KEY
- EMBEDDING_MODEL
- RERANKER_MODEL
- CORS_ORIGINS

## Important constraints

- Do not commit secret values.
- Do not fabricate experimental results.
- Do not fabricate citations or page numbers.
- Use evidence-grounded answers only.
- Keep user document isolation as a mandatory requirement.

## Validation status

The current repository has been checked for the baseline health needed to continue:

- Python compilation of the backend package succeeded.
- Frontend production build succeeded with Vite.

This confirms the foundation is at least runnable and import-safe before deeper research implementation begins.

## Future work

The next major milestone is the complete data/auth foundation and retrieval pipeline, followed by the LangGraph orchestrator and verification system. The project will continue in phases to keep the stack correct, testable, and academically defensible.
│   │   │   ├── Chat.tsx               # Query interface
│   │   │   └── Upload.tsx             # Upload
│   │   ├── api/client.ts              # API client
│   │   ├── store/                     # Redux state
│   │   ├── App.tsx                    # Routing
│   │   └── main.tsx                   # Entry
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml                 # Dev environment
└── README.md
```

## Testing

### Test the Full Pipeline
```bash
# 1. Create admin account
cd backend
python create_admin.py testadmin test@example.com testpass

# 2. Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -d "username=testadmin&password=testpass" | jq -r '.access_token')

# 3. Upload a sample document
echo "This is a sample document about Retrieval-Augmented Generation (RAG)." > sample.txt
DOC_ID=$(curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.txt" | jq -r '.id')

# 4. Index the document
curl -X POST http://localhost:8000/api/embeddings/index/$DOC_ID \
  -H "Authorization: Bearer $TOKEN"

# 5. Run full RAG pipeline
curl -X POST http://localhost:8000/api/orchestrate/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 10}' | jq .
```

## Troubleshooting

### Backend crashes on start
```bash
# Check database exists
psql -l | grep trustrag

# Check environment variables
cat backend/.env

# View logs
docker logs trustrag-backend
```

### Frontend can't connect to API
- Ensure backend is running: `curl http://localhost:8000/healthz`
- Check CORS in `backend/app/main.py`
- Verify API_BASE_URL in `frontend/src/api/client.ts`

### Qdrant connection errors
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart trustrag-qdrant
```

### Document indexing fails
```bash
# Check storage directory
ls -la backend/storage/documents

# Check permissions
chmod 755 backend/storage/documents

# View embedding errors
docker logs trustrag-backend | grep -i embed
```

## Production Deployment

### Azure App Service + PostgreSQL
```bash
# Create infrastructure
az group create -n trustrag-prod -l eastus
az postgres server create -n trustrag-db -g trustrag-prod \
  --admin-user admin --admin-password <STRONG_PASSWORD>
az appservice plan create -n trustrag-plan -g trustrag-prod \
  --is-linux --sku B2
az webapp create -n trustrag-app -g trustrag-prod \
  -p trustrag-plan --runtime "PYTHON|3.11"

# Configure environment
az webapp config appsettings set --resource-group trustrag-prod \
  --name trustrag-app \
  --settings DATABASE_URL=postgresql://admin:...@trustrag-db.postgres.database.azure.com/trustrag \
  JWT_SECRET=<STRONG_SECRET> \
  QDRANT_URL=https://qdrant.trustrag.ai

# Deploy
git push azure main
```

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

- 📖 Docs: See inline code comments and API docs at `/docs`
- 🐛 Issues: GitHub Issues
- 💬 Questions: GitHub Discussions

---

**Built for trustworthy, explainable retrieval-augmented generation**
# TrustRag
