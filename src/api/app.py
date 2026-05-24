"""FastAPI application for the SRI RAG system."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.api.routes import query
from src.errors.rag_errors import RAGError
from src.errors.indexing_errors import IndexingError
from src.errors.retrieval_errors import RetrievalError
from src.errors.vector_db_errors import VectorDBError
from src.errors.llm_errors import LLMError, LLMModelNotFoundError

logger = logging.getLogger(__name__)



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
    }



app.include_router(query.router,prefix="/api")

