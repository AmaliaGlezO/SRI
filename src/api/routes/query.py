"""Query endpoints for the RAG API."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

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
_generator = None


def set_rag_pipeline(rag_pipeline):
    """Set the RAG pipeline instance for use by the endpoints."""
    global _rag_pipeline
    _rag_pipeline = rag_pipeline


def set_generator(generator):
    """Set the answer generator instance for direct LLM access."""
    global _generator
    _generator = generator


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
        init_rag_time=0
        result={}
        end_rag_time=0
        if request.use_rag:
            init_rag_time = datetime.now()
            result = await _rag_pipeline.retrieve(
                query=request.query,
                top_k=request.top_k,
                use_prf=request.use_prf,
                relevance_threshold=request.relevance_threshold,
                max_doc_chars=request.max_doc_chars,
                use_internet_search=request.use_internet_search,
            )
            end_rag_time = datetime.now()
        rag_time = (end_rag_time - init_rag_time).total_seconds()
        

        context = result.get("context", "")
        answer_generation_time = datetime.now()
        if _generator and request.use_rag:
            answer = await _generator.generate(context, request.query,request.temperature)
        elif _generator:
            answer = await _generator.generate_direct(request.query, request.temperature)
        else:
            answer = "Generator not available"
        end_answer_generation_time = datetime.now()
        answer_generation_time = (end_answer_generation_time - answer_generation_time).total_seconds()

        # Get token counts
        input_tokens = await _generator.get_token_count(context + " " + request.query) if _generator else 0
        output_tokens = await _generator.get_token_count(answer) if _generator else 0
        
        # Track stats
        from src.stats.stats import stats, QueryStats
        query_stats = QueryStats(
            session_id="default",
            query=request.query,
            timestamp=datetime.now().isoformat(),
            inference_time=answer_generation_time,
            token_in=input_tokens,
            token_out=output_tokens,
            char_truncated=0,
            total_context_truncated=0,
            rag_time=rag_time,
            internet_search_used=result.get("search_performed", False),
            top_k=request.top_k or 3,
            top_score=result.get("top_local_score", 0),
            num_sources=len(result.get("sources", [])),
            use_prf=request.use_prf,
            use_rag=request.use_rag,
        )
        try:
            stats.add_query(query_stats)
        except:
            pass
        
        return QueryResponse(
            query=result["query"],
            answer=answer,
            sources=result["sources"],
            search_performed=result["search_performed"],
            top_local_score=result["top_local_score"],
            retrieved_documents=result["retrieved_documents"],
            status=result.get("status", []),
            token_usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
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
        logger.error(f"Unexpected error in query endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        )


@router.get("/health", response_model=dict)
async def query_health() -> dict:
    """Check if query service is healthy."""
    return {"status": "healthy", "service": "query"}


@router.get("/stats/dashboard", response_model=dict)
async def get_dashboard() -> dict:
    """Get dashboard metrics - all stats in one endpoint."""
    from src.stats.stats import stats
    return stats.get_metrics_for_dashboard()


@router.get("/stats/global", response_model=dict)
async def get_global_stats() -> dict:
    """Get global stats."""
    from src.stats.stats import stats
    return stats.get_global()

@router.get("/stats/tokens", response_model=dict)
async def get_token_stats() -> dict:
    """Get global token stats."""
    from src.stats.stats import stats
    global_stats = stats.get_global()
    return {
        "total_input_tokens": global_stats.get("total_token_in", 0),
        "total_output_tokens": global_stats.get("total_token_out", 0),
        "total_tokens": global_stats.get("total_tokens", 0)
    }

@router.get("/stats/session/{session_id}", response_model=dict)
async def get_session_stats(session_id: str) -> dict:
    """Get session-specific stats."""
    from src.stats.stats import stats
    return stats.get_session_stats(session_id)


@router.get("/stats/sessions", response_model=list)
async def get_all_sessions() -> list:
    """Get all sessions summary."""
    from src.stats.stats import stats
    return stats.get_all_sessions()


@router.get("/stats/recent", response_model=list)
async def get_recent_queries(n: int = 10) -> list:
    """Get recent queries."""
    from src.stats.stats import stats
    return stats.get_recent_queries(n)


@router.get("/stats/session/{session_id}/details", response_model=dict)
async def get_session_details(session_id: str) -> dict:
    """Get detailed session stats."""
    from src.stats.stats import stats
    return stats.get_session_stats(session_id)


@router.post("/generate/direct", response_model=dict)
async def generate_direct(
    question: str,
    temperature: float | None = None,
) -> dict:
    """
    Generate answer directly using LLM without RAG retrieval.
    Useful for simple queries or when no context is needed.
    """
    if not _generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    
    try:
        answer = _generator.generate_direct(question, temperature)
        
        input_tokens = _generator.get_token_count(question)
        output_tokens = _generator.get_token_count(answer)
        
        return {
            "question": question,
            "answer": answer,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "mode": "direct",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")


@router.get("/health", response_model=dict)
async def query_health() -> dict:
    """Check if query service is healthy."""
    return {
        "status": "healthy", 
        "service": "query",
        "generator_available": _generator is not None,
    }

