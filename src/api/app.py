"""FastAPI application for the SRI RAG system."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.api.models import ErrorResponse
from src.api.routes import query, indexing, health
from src.errors.rag_errors import RAGError
from src.errors.indexing_errors import IndexingError
from src.errors.retrieval_errors import RetrievalError
from src.errors.vector_db_errors import VectorDBError
from src.errors.llm_errors import LLMError, LLMModelNotFoundError

logger = logging.getLogger(__name__)


# Global state
_rag_pipeline = None
_system_initializer = None
_status_checker = None


def init_api(rag_pipeline, system_initializer, status_checker):
    """Initialize API with dependencies."""
    global _rag_pipeline, _system_initializer, _status_checker

    _rag_pipeline = rag_pipeline
    _system_initializer = system_initializer
    _status_checker = status_checker

    # Inject dependencies into routers
    query.set_rag_pipeline(rag_pipeline)
    indexing.set_system_initializer(system_initializer)
    health.set_status_checker(status_checker)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("SRI RAG API starting up...")
    yield
    logger.info("SRI RAG API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SRI RAG System API",
    description="REST API for the Spanish Information Retrieval RAG System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ErrorResponse)
async def response_error_handler(request:Request,exc:ErrorResponse):
    """Handle ErrorResponse"""
    logger.error(f"Error Response: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error_type':exc.__class__.__name__,
            "message":str(exc),
        }
    )

@app.exception_handler(RAGError)
async def rag_error_handler(request: Request, exc: RAGError):
    """Handle RAG-specific errors."""
    logger.error(f"RAG Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(IndexingError)
async def indexing_error_handler(request: Request, exc: IndexingError):
    """Handle indexing-specific errors."""
    logger.error(f"Indexing Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(RetrievalError)
async def retrieval_error_handler(request: Request, exc: RetrievalError):
    """Handle retrieval-specific errors."""
    logger.error(f"Retrieval Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(VectorDBError)
async def vector_db_error_handler(request: Request, exc: VectorDBError):
    """Handle vector DB-specific errors."""
    logger.error(f"Vector DB Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(LLMModelNotFoundError)
async def llm_model_not_found_handler(request: Request, exc: LLMModelNotFoundError):
    """Handle LLM model not found errors."""
    logger.error(f"LLM Model Not Found: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    """Handle LLM-specific errors."""
    logger.error(f"LLM Error: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred",
        },
    )




@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SRI RAG System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status_endpoint": "/status",
        "health_endpoint": "/health",
    }



app.include_router(query.router)
app.include_router(indexing.router)
app.include_router(health.router)
