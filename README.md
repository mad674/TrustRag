# TrustRAG - Production-Ready RAG with Multi-Agent Orchestration

A complete Retrieval-Augmented Generation (RAG) system with:
- **JWT Authentication** with role-based access control
- **Document Management** with secure upload and storage
- **Intelligent Embedding** with caching and provider selection
- **Hybrid Retrieval** combining BM25 (lexical) + Dense (semantic) search
- **Multi-Agent Orchestration** using LangGraph for answer generation, verification, and reporting
- **Production Docker Setup** with PostgreSQL, Qdrant, backend, and frontend

## Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- Python 3.11+ (for local development)

### Using Docker Compose (Recommended - 1 Command)
```bash
cd /path/to/TrustRAG
docker-compose up -d
```

Wait 30s for services to start:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Backend: http://localhost:8000
- Qdrant: http://localhost:6333

**Default Admin Credentials:**
- Username: `admin`
- Password: `password123`

### Local Development Setup
```bash
# 1. Create database
psql -U postgres -c "CREATE DATABASE trustrag;"
psql -U postgres -c "CREATE USER trustrag WITH PASSWORD 'trustrag';"

# 2. Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create admin user
python create_admin.py admin admin@example.com password123

# 4. Start backend
python -m uvicorn app.main:app --reload

# 5. In new terminal - Install frontend
cd frontend
npm install
npm run dev

# 6. Start Qdrant (if not using Docker)
# Download from https://github.com/qdrant/qdrant
qdrant --http-port 6333
```

Access at http://localhost:5173

## Core Features

### 1. Authentication & RBAC
- JWT token-based authentication
- Secure password hashing with bcrypt
- Role-based access control (admin/user)

### 2. Document Management
- Secure file upload with validation
- Automatic document indexing
- File storage with cleanup

### 3. Adaptive Retrieval
- **Intent Classification**: Detects query type (QA, Definition, Summary, etc.)
- **Hybrid Search**: BM25 (lexical) + Dense (Qdrant semantic)
- **Cross-Encoder Reranking**: Refines results

### 4. Multi-Agent Pipeline (LangGraph)
1. **QA Agent** → Generates answer from context
2. **Citation Agent** → Extracts source documents
3. **Verification Agent** → Validates answer grounding
4. **Summary Agent** → Summarizes documents
5. **Explainability Agent** → Explains reasoning
6. **Report Agent** → Creates downloadable report

### 5. Embedding Service
- sentence-transformers (offline, fast)
- OpenAI API (production-grade)
- SQLite caching for efficiency

### 6. Evaluation Metrics
- Precision@K, Recall@K
- Mean Reciprocal Rank
- NDCG (Normalized DCG)
- Hallucination Detection

## API Endpoints

### Auth
```bash
# Register user
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "email": "user1@example.com",
    "password": "password123"
  }'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password123" | jq -r '.access_token')

# Get current user
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/users/me
```

### Documents
```bash
# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# Index document for search
curl -X POST http://localhost:8000/api/embeddings/index/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Retrieval
```bash
# Vector search only
curl -X POST http://localhost:8000/api/retrieve/vector \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 10}'

# Adaptive hybrid retrieval
curl -X POST http://localhost:8000/api/adaptive/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain RAG", "top_k": 10}'
```

### Full RAG Pipeline (All Agents)
```bash
# Complete end-to-end orchestration
curl -X POST http://localhost:8000/api/orchestrate/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 10}'
```

Interactive API docs: http://localhost:8000/docs

## Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://trustrag:trustrag@localhost:5432/trustrag

# Vector Database
QDRANT_URL=http://localhost:6333

# JWT Secret (change in production!)
JWT_SECRET=your-secret-key-here

# Embedding Provider
EMBEDDING_PROVIDER=sentence-transformers  # Options: sentence-transformers, openai, fallback
OPENAI_API_KEY=sk-...  # Only if using OpenAI
EMBEDDING_BATCH_SIZE=32

# File Storage
UPLOAD_DIR=./storage/documents

# Logging
LOG_LEVEL=INFO
```

## Project Structure

```
TrustRAG/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app
│   │   ├── auth.py                    # JWT auth
│   │   ├── config.py                  # Settings
│   │   ├── models.py                  # DB models
│   │   ├── db.py                      # Database
│   │   ├── api/
│   │   │   ├── auth.py                # /api/auth
│   │   │   ├── users.py               # /api/users
│   │   │   ├── documents.py           # /api/documents
│   │   │   ├── embeddings.py          # /api/embeddings
│   │   │   ├── retrieve.py            # /api/retrieve
│   │   │   ├── adaptive.py            # /api/adaptive
│   │   │   └── orchestrate.py         # /api/orchestrate (full RAG)
│   ├── services/
│   │   ├── embedding_service/         # Embeddings with caching
│   │   ├── adaptive_retrieval/        # BM25 + dense + rerank
│   │   ├── langgraph/                 # Multi-agent orchestration
│   │   │   ├── state.py               # State definition
│   │   │   ├── agents.py              # Agent implementations
│   │   │   └── orchestrator.py        # StateGraph coordinator
│   │   └── evaluation/                # Evaluation metrics
│   ├── create_admin.py                # Create admin user
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx              # Login
│   │   │   ├── Register.tsx           # Register
│   │   │   ├── Dashboard.tsx          # Doc library
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
#   T r u s t R a g  
 