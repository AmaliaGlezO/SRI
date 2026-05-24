import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def _get_env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_env_int(key: str, default: int) -> int:
    """Parse integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Parse float environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_env_str(key: str, default: str = "") -> str:
    """Get string environment variable."""
    return os.getenv(key, default)


# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
INDEXES_DIR = BASE_DIR / "indexes"
DATA_DIR = BASE_DIR / "data"

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Default model URL for HuggingFace download
DEFAULT_MODEL_HF_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
DEFAULT_MODEL_FILE = "TinyLlama-1.1B-Chat-v1.0-Q4_K_M.gguf"
DEFAULT_MODEL_URL = f"https://huggingface.co/{DEFAULT_MODEL_HF_REPO}/resolve/main/{DEFAULT_MODEL_FILE}".lower()

# Model path - if empty, will use default and download if needed
MODEL_PATH: Optional[str] = _get_env_str("MODEL_PATH", "")

# LLM parameters
MODEL_TEMPERATURE = _get_env_float("MODEL_TEMPERATURE", 0.3)
MODEL_MAX_TOKENS = _get_env_int("MODEL_MAX_TOKENS", 2048)
MODEL_N_CTX = _get_env_int("MODEL_N_CTX", 2048)
MODEL_N_THREADS: Optional[int] = _get_env_int(
    "MODEL_N_THREADS", None
)  # None = auto-detect
MODEL_VERBOSE = _get_env_bool("MODEL_VERBOSE", False)
USE_GPU = _get_env_bool("USE_GPU", False)

# ============================================================================
# RAG CONFIGURATION
# ============================================================================

# Relevance threshold for triggering web search
RAG_RELEVANCE_THRESHOLD = _get_env_float("RAG_RELEVANCE_THRESHOLD", 0.4)

# Query expansion settings
RAG_ENABLE_QUERY_EXPANSION = _get_env_bool("RAG_ENABLE_QUERY_EXPANSION", True)
RAG_QUERY_EXPANSION_TERMS = _get_env_int("RAG_QUERY_EXPANSION_TERMS", 10)
RAG_COOCCURRENCE_WINDOW = _get_env_int("RAG_COOCCURRENCE_WINDOW", 1)

# Retriever weights (LM vs Vector)
RAG_LM_RETRIEVER_WEIGHT = _get_env_float("RAG_LM_RETRIEVER_WEIGHT", 0.5)
RAG_MAX_DOC_CHARS = int(os.environ.get("RAG_MAX_DOC_CHARS",3500))
RAG_VECTOR_RETRIEVER_WEIGHT = _get_env_float("RAG_VECTOR_RETRIEVER_WEIGHT", 0.5)

# Ranker weights (configurable via env vars)
RANKER_RELEVANCE_WEIGHT = _get_env_float("RANKER_RELEVANCE_WEIGHT", 0.5)
RANKER_POPULARITY_WEIGHT = _get_env_float("RANKER_POPULARITY_WEIGHT", 0.15)
RANKER_FRESHNESS_WEIGHT = _get_env_float("RANKER_FRESHNESS_WEIGHT", 0.2)
RANKER_COMPLETENESS_WEIGHT = _get_env_float("RANKER_COMPLETENESS_WEIGHT", 0.1)
RANKER_SOURCE_QUALITY_WEIGHT = _get_env_float("RANKER_SOURCE_QUALITY_WEIGHT", 0.05)

# Trusted domains for ranking
RANKER_TRUSTED_DOMAINS = _get_env_str(
    "RANKER_TRUSTED_DOMAINS",
    "stackoverflow.com,github.com,mdn.io,docs.python.org,xataka.com"
).split(",")

# Presentation badges
PRESENTATION_BADGES = {
    "tech_news": {"label": "Noticia", "color": "blue"},
    "encyclopedia": {"label": "Enciclopedia", "color": "green"},
    "documentation": {"label": "Docs", "color": "purple"},
    "video": {"label": "Video", "color": "red"},
    "web": {"label": "Web", "color": "gray"},
}

# Number of documents to retrieve
RAG_RETRIEVER_K = _get_env_int("RAG_RETRIEVER_K", 3)

# ============================================================================
# VECTOR DB CONFIGURATION
# ============================================================================

VECTOR_DB_COLLECTION_NAME = _get_env_str(
    "VECTOR_DB_COLLECTION_NAME", "sri_documents_transformer"
)
VECTOR_DB_PERSIST_DIR = str((INDEXES_DIR / "chroma_langchain").absolute())
VECTOR_DB_TOP_K = _get_env_int("VECTOR_DB_TOP_K", 10)
BATCH_SIZE = _get_env_int("BATCH_SIZE",5000)
RESET= _get_env_bool("RESET",False)
# ============================================================================
# WEB SEARCH CONFIGURATION
# ============================================================================

WEB_SEARCH_ENGINE = _get_env_str("WEB_SEARCH_ENGINE", "duckduckgo")
WEB_SEARCH_MAX_RESULTS = _get_env_int("WEB_SEARCH_MAX_RESULTS", 5)
WEB_SEARCH_REGION = _get_env_str("WEB_SEARCH_REGION", "es-es")
WEB_SEARCH_TIME = _get_env_str("WEB_SEARCH_TIME", "y")

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_HOST = _get_env_str("API_HOST", "0.0.0.0")
API_PORT = _get_env_int("API_PORT", 8000)
API_CORS_ORIGINS = _get_env_str("API_CORS_ORIGINS", "*").split(",")
FORCE = _get_env_bool("FORCE",False)
# ====================================
# ========================================
# INDEXING CONFIGURATION
# ============================================================================
CHUNK_SIZE=_get_env_int("CHUNK_SIZE", 1500)
CHUNK_OVERLAP=_get_env_int("CHUNK_OVERLAP", 100)
STRATEGY=_get_env_str("STRATEGY", "sliding")
MIN_CHUNK_SIZE=_get_env_int("MIN_CHUNK_SIZE", 100)

INDEX_LANGUAGE = _get_env_str("INDEX_LANGUAGE", "spanish")
INDEX_SAVE_DIR = str((INDEXES_DIR).absolute())
#LMretrieval
MU = _get_env_float("MU",2000.0)

#TFIDF Fallback
MAX_FEATURES = _get_env_int("MAX_FEATURES", 15000)

DEFAULT_TIMEOUT = _get_env_int(os.getenv("DEFAULT_TIMEOUT",15),15)


ALPHA = _get_env_float(os.getenv("ALPHA",1.0),1.0)
BETA = _get_env_float(os.getenv("BETA",0.75),0.75)
GAMMA =_get_env_float(os.getenv("GAMMA",0.15),0.15)