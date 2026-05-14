# SRI RAG System

Spanish Information Retrieval system using RAG (Retrieval-Augmented Generation) with hybrid search (LM + Vector) and automatic web search fallback.

## Features

- **Hybrid Retrieval**: Combines language model (LM) and vector database retrieval
- **Automatic Web Search**: Falls back to internet search when local results are not relevant
- **Configurable via Environment Variables**: All settings can be customized
- **Automatic Model Download**: Downloads default model if not present
- **Spanish Language Support**: Optimized for Spanish queries and documents
- **REST API**: FastAPI-based API for easy integration

## Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Or using the setup script
./setup.sh
```

## Configuration

The system can be configured via environment variables. Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

### Environment Variables

#### Model Configuration

- `MODEL_PATH`: Path to model file (empty = use default TinyLlama, will download if missing)
- `MODEL_TEMPERATURE`: LLM sampling temperature (default: 0.3)
- `MODEL_MAX_TOKENS`: Maximum tokens to generate (default: 2048)
- `MODEL_N_CTX`: Context window size (default: 2048)
- `MODEL_N_THREADS`: Number of CPU threads (default: auto-detect)
- `MODEL_VERBOSE`: Enable verbose LLM output (default: false)

#### RAG Configuration

- `RAG_RELEVANCE_THRESHOLD`: Threshold for triggering web search (0.0-1.0, default: 0.4)
- `RAG_ENABLE_PRF`: Enable Pseudo-Relevance Feedback for query expansion (default: true)
- `RAG_PRF_K`: Number of top documents for PRF (default: 5)
- `RAG_PRF_TERMS`: Number of terms to expand (default: 10)
- `RAG_LM_RETRIEVER_WEIGHT`: Weight for LM retriever (default: 0.5)
- `RAG_VECTOR_RETRIEVER_WEIGHT`: Weight for vector retriever (default: 0.5)
- `RAG_RETRIEVER_K`: Number of documents to retrieve (default: 5)

#### Vector DB Configuration

- `VECTOR_DB_COLLECTION_NAME`: Chroma collection name (default: sri_documents_transformer)
- `VECTOR_DB_PERSIST_DIR`: Directory for vector store persistence (default: indexes/chroma_langchain)
- `VECTOR_DB_TOP_K`: Number of results for vector search (default: 10)

#### Web Search Configuration

- `WEB_SEARCH_MAX_RESULTS`: Maximum web search results (default: 5)
- `WEB_SEARCH_REGION`: Search region (default: es-es)
- `WEB_SEARCH_TIME`: Time filter (default: y)

#### API Configuration

- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `API_CORS_ORIGINS`: CORS allowed origins (default: *)

## Running the Application

### Start the API Server

```bash
# Using the launcher
python api.py

# Or directly
python -m src.api.server
```

The API will be available at:

- API: <http://localhost:8000>
- Documentation: <http://localhost:8000/docs>
- Alternative docs: <http://localhost:8000/redoc>

### API Endpoints

#### Query the RAG System

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es el procesamiento de lenguaje natural?"}'
```

Response includes:

- `answer`: Generated answer
- `sources`: Source documents
- `search_performed`: Whether web search was used
- `top_local_score`: Relevance score of best local result
- `retrieved_documents`: List of retrieved documents with scores

## Behavior Documentation

### Model Handling

- **Default Model**: If `MODEL_PATH` is empty, the system uses the default TinyLlama model
- **Auto-Download**: The default model is automatically downloaded if not present
- **Custom Model**: If `MODEL_PATH` is provided, the model must exist or an error is raised
- **Error**: `LLMModelNotFoundError` is raised if a custom model path is provided but the file doesn't exist

### Offline / No Internet Scenarios

- **Web Search Failure**: If internet search fails (no connection, timeout, etc.), the system:
  - Logs the error
  - Continues with local results only
  - Returns answer based on available local documents
- **No Relevant Local Results**: If local documents have low relevance scores:
  - Web search is attempted
  - If web search fails, the system uses local results anyway
  - The answer may indicate insufficient information

### Error Handling

The API has comprehensive error handling:

- `RAGError`: General RAG pipeline errors (500)
- `IndexingError`: Document indexing errors (500)
- `RetrievalError`: Document retrieval errors (500)
- `VectorDBError`: Vector database errors (500)
- `LLMError`: LLM operation errors (503)
- `LLMModelNotFoundError`: Model not found (503)
- `WebSearchExecutionError`: Web search failure (500)
- `Exception`: Unexpected errors (500)

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
│   ├── utils/                 # Utilities (model downloader)
│   └── vector_db/             # Vector database
├── data/                      # Document storage
├── indexes/                   # Index storage
├── models/                    # Model files
└── tests/                     # Tests
```

## Development

### Running Tests

```bash
pytest
```

### Adding Documents

Documents are stored in the `data/` directory. The system automatically indexes them on startup.

## License

See LICENSE file.
