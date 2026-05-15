"""Query endpoints for the RAG API."""

from fastapi import APIRouter, HTTPException, Query

from src.api.models import QueryRequest, QueryResponse, ErrorResponse
from src.errors.rag_errors import (
    RAGError,
    RAGPipelineInitializationError,
    RAGRetrievalError,
    RAGAnswerGenerationError,
)
from src.errors.internet_search_error import WebSearchExecutionError

router = APIRouter(prefix="/query", tags=["Query"])


_rag_pipeline = None


def set_rag_pipeline(rag_pipeline):
    """Set the RAG pipeline instance for use by the endpoints."""
    global _rag_pipeline
    _rag_pipeline = rag_pipeline


@router.post(
    "",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Query the RAG system for an answer.
    
    - **query**: User query in Spanish
    - **use_rag**: Whether to use the configurable RAG flow
    - **top_k**: Number of documents to retrieve (1-50)
    - **temperature**: Optional LLM temperature override
    - **relevance_threshold**: Optional relevance threshold override
    - **max_doc_chars**: Optional document truncation limit
    - **use_prf**: Whether to use pseudo-relevance feedback
    - **use_internet_search**: Whether to allow internet fallback search
    """
    if not _rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized",
        )

    try:
        result = _rag_pipeline.answer(
            query=request.query,
            use_rag=request.use_rag,
            top_k=request.top_k,
            use_prf=request.use_prf,
            temperature=request.temperature,
            relevance_threshold=request.relevance_threshold,
            max_doc_chars=request.max_doc_chars,
            use_internet_search=request.use_internet_search,
        )

        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"],
            search_performed=result["search_performed"],
            top_local_score=result["top_local_score"],
            retrieved_documents=result["retrieved_documents"],
        )
    except RAGRetrievalError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {exc}",
        )
    except RAGAnswerGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Answer generation failed: {exc}",
        )
    except RAGPipelineInitializationError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Pipeline not properly initialized: {exc}",
        )
    except RAGError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG error: {exc}",
        )
    except WebSearchExecutionError as exc:
        raise HTTPException(
            status_code=500,
            detail=f'no internet: {exc}'
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        )


@router.get("/health", response_model=dict)
async def query_health() -> dict:
    """Check if query service is healthy."""
    return {"status": "healthy", "service": "query"}
