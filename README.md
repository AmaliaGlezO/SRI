# SRI RAG System

Spanish Information Retrieval system using RAG (Retrieval-Augmented Generation) with hybrid search (LM + Vector) and automatic web search fallback.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for UI)
- uv
- 4GB+ RAM minimum (8GB+ recommended)
- 2GB+ free disk space for model

## Installation

```bash
# Install Python dependencies
uv sync

# Configure environment variables (optional - defaults work out of the box)
cp .env.example .env

# Install UI dependencies (optional)
cd ui
pnpm install 
cd ..
```

## Running the Application

### API Server

```bash
python api.py
```

The API will be available at:

- API: <http://localhost:8000>
- Documentation: <http://localhost:8000/docs>
- Health Check: <http://localhost:8000/health>

### Web UI

```bash
# Terminal 1: Start the API server
uv run api.py

# Terminal 2: Start the UI
cd ui
npm run dev
```

The UI will be available at: <http://localhost:5173>

## Configuration

The system can be configured via environment variables in the `.env` file. Copy `.env.example` to `.env` and adjust values as needed.

### Environment Variables

**Model Configuration**

- `MODEL_PATH`: Path to model file (empty = use default TinyLlama, will download if missing)
- `MODEL_TEMPERATURE`: LLM sampling temperature (default: 0.3)
- `MODEL_MAX_TOKENS`: Maximum tokens to generate (default: 2048)
- `MODEL_N_CTX`: Context window size (default: 2048)
- `MODEL_N_THREADS`: Number of CPU threads (default: auto-detect)
- `MODEL_VERBOSE`: Enable verbose LLM output (default: false)
- `USE_GPU`: Enable GPU acceleration (default: false)

**RAG Configuration**

- `RAG_RELEVANCE_THRESHOLD`: Threshold for triggering web search (0.0-1.0, default: 0.4)
- `RAG_ENABLE_PRF`: Enable Pseudo-Relevance Feedback (default: true)
- `RAG_PRF_K`: Number of top documents for PRF (default: 5)
- `RAG_PRF_TERMS`: Number of terms to expand (default: 10)
- `RAG_LM_RETRIEVER_WEIGHT`: Weight for LM retriever (default: 0.5)
- `RAG_VECTOR_RETRIEVER_WEIGHT`: Weight for vector retriever (default: 0.5)
- `RAG_RETRIEVER_K`: Number of documents to retrieve (default: 5)

**Vector DB Configuration**

- `VECTOR_DB_COLLECTION_NAME`: Chroma collection name (default: sri_documents_transformer)
- `VECTOR_DB_PERSIST_DIR`: Directory for vector store persistence (default: indexes/chroma_langchain)
- `VECTOR_DB_TOP_K`: Number of results for vector search (default: 10)

**Web Search Configuration**

- `WEB_SEARCH_MAX_RESULTS`: Maximum web search results (default: 5)
- `WEB_SEARCH_REGION`: Search region (default: es-es)
- `WEB_SEARCH_TIME`: Time filter (default: y)

**API Configuration**

- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `API_CORS_ORIGINS`: CORS allowed origins (default: *)

## Adding Documents

Documents are stored in the `data/` directory. The system automatically indexes them on startup.

## Project Structure

```
SRI/
├── src/
│   ├── config.py              # Centralized configuration
│   ├── api/                   # FastAPI application
│   ├── generator/             # LLM wrapper
│   ├── indexing/              # Document indexing
│   ├── rag/                   # RAG pipeline
│   ├── retrieval/             # Retrieval components
│   ├── search_internet/       # Web search
│   ├── utils/                 # Utilities
│   └── vector_db/             # Vector database
├── ui/                        # React web interface
├── data/                      # Document storage
├── indexes/                   # Index storage
└── models/                    # Model files
