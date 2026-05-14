

import os
from pathlib import Path
from typing import Optional


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
DEFAULT_MODEL_FILE = "TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
DEFAULT_MODEL_URL = f"https://huggingface.co/{DEFAULT_MODEL_HF_REPO}/resolve/main/{DEFAULT_MODEL_FILE}"

# Model path - if empty, will use default and download if needed
MODEL_PATH: Optional[str] = _get_env_str("MODEL_PATH", "")

# LLM parameters
MODEL_TEMPERATURE = _get_env_float("MODEL_TEMPERATURE", 0.3)
MODEL_MAX_TOKENS = _get_env_int("MODEL_MAX_TOKENS", 2048)
MODEL_N_CTX = _get_env_int("MODEL_N_CTX", 2048)
MODEL_N_THREADS: Optional[int] = _get_env_int("MODEL_N_THREADS", None)  # None = auto-detect
MODEL_VERBOSE = _get_env_bool("MODEL_VERBOSE", False)

# ============================================================================
# RAG CONFIGURATION
# ============================================================================

# Relevance threshold for triggering web search
RAG_RELEVANCE_THRESHOLD = _get_env_float("RAG_RELEVANCE_THRESHOLD", 0.4)

# Pseudo-Relevance Feedback (PRF) settings
RAG_ENABLE_PRF = _get_env_bool("RAG_ENABLE_PRF", True)
RAG_PRF_K = _get_env_int("RAG_PRF_K", 5)
RAG_PRF_TERMS = _get_env_int("RAG_PRF_TERMS", 10)

# Retriever weights (LM vs Vector)
RAG_LM_RETRIEVER_WEIGHT = _get_env_float("RAG_LM_RETRIEVER_WEIGHT", 0.5)
RAG_VECTOR_RETRIEVER_WEIGHT = _get_env_float("RAG_VECTOR_RETRIEVER_WEIGHT", 0.5)

# Number of documents to retrieve
RAG_RETRIEVER_K = _get_env_int("RAG_RETRIEVER_K", 5)

# ============================================================================
# VECTOR DB CONFIGURATION
# ============================================================================

VECTOR_DB_COLLECTION_NAME = _get_env_str("VECTOR_DB_COLLECTION_NAME", "sri_documents_transformer")
VECTOR_DB_PERSIST_DIR = str((INDEXES_DIR / "chroma_langchain").absolute())
VECTOR_DB_TOP_K = _get_env_int("VECTOR_DB_TOP_K", 10)

# ============================================================================
# WEB SEARCH CONFIGURATION
# ============================================================================

WEB_SEARCH_MAX_RESULTS = _get_env_int("WEB_SEARCH_MAX_RESULTS", 5)
WEB_SEARCH_REGION = _get_env_str("WEB_SEARCH_REGION", "es-es")
WEB_SEARCH_TIME = _get_env_str("WEB_SEARCH_TIME", "y")

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_HOST = _get_env_str("API_HOST", "0.0.0.0")
API_PORT = _get_env_int("API_PORT", 8000)
API_CORS_ORIGINS = _get_env_str("API_CORS_ORIGINS", "*").split(",")

# ============================================================================
# INDEXING CONFIGURATION
# ============================================================================

INDEX_LANGUAGE = _get_env_str("INDEX_LANGUAGE", "spanish")
INDEX_SAVE_DIR = str((INDEXES_DIR).absolute())
