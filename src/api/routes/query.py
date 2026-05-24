
import logging
from fastapi import APIRouter, HTTPException
logger = logging.getLogger(__name__)
from typing import Dict,Any
from src.api.models import QueryRequest, QueryResponse,ErrorResponse,FeedbackRequest,FeedbackResponse
from src.errors.rag_errors import (
    RAGError,
    RAGPipelineInitializationError,
    RAGRetrievalError,
    RAGAnswerGenerationError,
)
from src.errors.internet_search_error import WebSearchExecutionError



_session_store: Dict[str, Dict[str, Any]] = {}
router = APIRouter(prefix="/query", tags=["Query"])
globals = {}

def set_dependencies(globals_dict):
    """Set dependencies from the main server."""
    globals.update(globals_dict)
    
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
    - **use_query_expansion**: Whether to use co-occurrence query expansion
    - **use_internet_search**: Whether to allow internet fallback search
    """
    logger.info(f"query: {request.query} top_k: {request.top_k} use_internet: {request.use_internet_search}")
    if not globals['_rag_pipeline']:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized",
        )
    
    try:
  
        result = {
            "query": request.query,
            "documents_retrieved": [],
            "top_local_score": 0.0,
    
        }
        
        if request.use_rag:
            result = await globals['_rag_pipeline'].retrieve(
                query=request.query,
                chunker=globals['chunker'],
                top_k=request.top_k,
                use_expand=request.use_query_expansion,
                relevance_threshold=request.relevance_threshold,
                max_doc_chars=request.max_doc_chars,
                use_internet_search=request.use_internet_search,
            )
        import time
        _session_id  = str(time.time())
        _session_store[_session_id] = {
            "original_query": request.query,
            "expanded_query":result.get('expanded_query',''),
            "original_docs": result.get("documents", []),
            "created_at": __import__('datetime').datetime.now()
        }
        return QueryResponse(
            query=result["query"],
            expanded_query=result.get("expanded_query",""),
            documents_retrieved= result.get("documents", []),
            top_local_score=result["top_local_score"],
            session_id=_session_id, 
            
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


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid feedback data"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Apply Rocchio relevance feedback to improve retrieval.
    """
    if not globals.get('_rag_pipeline'):
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    if not globals.get('_text_normalizer'):
        raise HTTPException(status_code=503, detail="Text normalizer not initialized")
    
    try:
        original_query = request.original_query
        original_docs = []
        
        # Obtener datos de la sesión
        if request.session_id in _session_store:
            session_data = _session_store[request.session_id]
            if not original_query:
                original_query = session_data.get("expanded_query") or session_data.get("original_query")
            original_docs = session_data.get("original_docs", [])
        elif not original_query:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found and no original_query provided",
            )
        
        relevant_texts = []
        non_relevant_texts = []
        
        doc_map = {}
        for doc in original_docs:
        
            if hasattr(doc, 'id'):  
                doc_id = doc.id if doc.id else None
                
                if not doc_id and hasattr(doc, 'metadata'):
                    doc_id = doc.metadata.get('url') or doc.metadata.get('source')
                
                # Obtener texto
                doc_text = doc.page_content if hasattr(doc, 'page_content') else ""
                
            elif isinstance(doc, dict):  # Es un diccionario
                doc_id = doc.get("id") or doc.get("doc_id")
                if not doc_id and "metadata" in doc:
                    doc_id = doc["metadata"].get("url") or doc["metadata"].get("source")
                doc_text = doc.get("content") or doc.get("text") or doc.get("page_content", "")
            else:
                continue  # Saltar si no es ni dict ni Document
            
            if doc_id and doc_text:
                doc_map[doc_id] = doc_text
        
        # Clasificar documentos relevantes y no relevantes
        for doc_id in request.relevant_docs:
            if doc_id in doc_map and doc_map[doc_id]:
                relevant_texts.append(doc_map[doc_id])
        
        for doc_id in request.non_relevant_docs:
            if doc_id in doc_map and doc_map[doc_id]:
                non_relevant_texts.append(doc_map[doc_id])
        
        # Aplicar Rocchio
        rocchio = globals.get('rocchio')
        if not rocchio:
            raise HTTPException(status_code=500, detail="Rocchio not initialized")
        
        reformulated_query_weights = rocchio.reformulate(
            original_query=original_query,
            relevant_docs=relevant_texts,
            non_relevant_docs=non_relevant_texts,
        )
        
        top_terms = sorted(
            reformulated_query_weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20]
        
        expanded_query = " ".join([term for term, _ in top_terms])
        
        # Realizar nueva búsqueda
        search_result = await globals['_rag_pipeline'].retrieve(
            query=expanded_query,
            chunker=globals['chunker'],
            top_k=request.top_k,
            use_expand=False,
            relevance_threshold=0.6,
            max_doc_chars=None,
            use_internet_search=True,
        )
        
        # Generar contexto y respuesta
        context = await get_context(search_result.get('documents', []))
        answer = await globals['_generator'].generate(context, original_query)
        logger.info(f"Anwser generated")
        serialized_docs = []
        for doc in search_result.get("documents", []):
            if hasattr(doc, 'page_content'):  # LangChain Document
                serialized_docs.append({
                    "id": getattr(doc, 'id', None) or doc.metadata.get('url', ''),
                    "text": doc.page_content,
                    "content": doc.page_content,
                    "url": doc.metadata.get('url', ''),
                    "title": doc.metadata.get('title', 'Sin título'),
                    "source": doc.metadata.get('source', 'Internet'),
                    "score": doc.metadata.get('score', 0),
                    "metadata": doc.metadata
                })
            elif isinstance(doc, dict):  # Ya es diccionario
                serialized_docs.append(doc)
            else:
                serialized_docs.append({"content": str(doc)})
        
        if request.session_id in _session_store:
            del _session_store[request.session_id]
        
        return FeedbackResponse(
            answer=answer,
            retrieved_docs=serialized_docs,
            reformulated_query=dict(top_terms),
            session_id=request.session_id,
        )
        
    except RAGRetrievalError as exc:
        raise HTTPException(status_code=500, detail=f"Retrieval failed after feedback: {exc}")
    except RAGAnswerGenerationError as exc:
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error in feedback endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")


async def get_context(docs):
    """Genera contexto a partir de documentos (pueden ser dict o LangChain Document)."""
    if not docs:
        return ""
    
    context_parts = []
    for doc in docs:
        # Extraer texto según el tipo de documento
        if hasattr(doc, 'page_content'):  # LangChain Document
            doc_text = doc.page_content
        elif isinstance(doc, dict):  # Diccionario
            doc_text = doc.get("content") or doc.get("text") or doc.get("page_content", "")
        else:
            continue
        
        if doc_text:
         
            context_parts.append(doc_text)
    
    return "\n\n---\n\n".join(context_parts)