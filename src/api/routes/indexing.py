"""Indexing endpoints for the RAG API."""

from fastapi import APIRouter, HTTPException
from src.api.models import IndexingRequest, IndexingResponse, ErrorResponse
from src.errors.indexing_errors import IndexingError
from src.errors.vector_db_errors import VectorDBError

router = APIRouter(prefix="/index", tags=["Indexing"])

# These will be injected by the app
_system_initializer = None


def set_system_initializer(initializer_func):
    """Set the system initializer function for use by the endpoints."""
    global _system_initializer
    _system_initializer = initializer_func


@router.post(
    "/rebuild",
    response_model=IndexingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Indexing failed"},
    },
)
async def rebuild_index(request: IndexingRequest) -> IndexingResponse:
    """
    Rebuild the local indexes (LM retriever + vector store).
    
    - **force**: If True, force rebuild even if index exists
    """
    if not _system_initializer:
        raise HTTPException(
            status_code=503,
            detail="System not initialized",
        )

    try:
        lm_retriever, vector_store = _system_initializer(force=request.force)

        return IndexingResponse(
            status="success",
            num_documents=lm_retriever.stats()["num_documents"],
            vocabulary_size=lm_retriever.stats()["vocabulary_size"],
            message=f"Successfully indexed {lm_retriever.stats()['num_documents']} documents",
        )
    except (IndexingError, VectorDBError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during indexing: {exc}",
        )


@router.get("/health", response_model=dict)
async def indexing_health() -> dict:
    """Check if indexing service is healthy."""
    return {"status": "healthy", "service": "indexing"}
