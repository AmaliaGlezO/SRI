"""Pydantic models for API request/response schemas."""

from typing import List, Optional,Dict,Any
from pydantic import BaseModel, Field


class RetrievedDocument(BaseModel):
    """A document retrieved during search."""

    title: str
    url: str
    source: str
    score: Optional[float] = None
    content: Optional[str] = None


class SourceInfo(BaseModel):
    """Information about a source used in answer generation."""

    title: str
    url: str
    source: str




class QueryRequest(BaseModel):
    """Request model for a query.
    
    Supports two phases:
    - Phase 1: Initial retrieval with optional co-occurrence expansion
    - Phase 2: Rocchio reformulation + re-retrieval + generation (when feedback_data is provided)
    """

    query: str = Field(..., description="User query in Spanish")
    use_rag: bool = Field(default=True, description="Whether to use the configurable RAG flow")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of documents to retrieve")
    temperature: Optional[float] = Field(default=None, description="LLM temperature")
    relevance_threshold: Optional[float] = Field(default=None, description="RAG relevance threshold")
    max_doc_chars: Optional[int] = Field(default=None, description="Max characters per document")
    use_query_expansion: bool = Field(
        default=True,
        description="Whether to use co-occurrence query expansion (phase 1 only)",
    )
    use_internet_search: bool = Field(
        default=True,
        description="Whether to allow internet search fallback when local relevance is low",
    )
 



class QueryResponse(BaseModel):
    """Response model for a query.
    """

    query: str = Field(description="Original user query")
    expanded_query:str =Field(default="",description="expanded query")
    top_local_score: float = Field(default=0.0, description="Relevance score of top local result")
    documents_retrieved: List = Field(default_factory=list, description="retrieved documents")  
    session_id: Optional[str] = None  




class ErrorResponse(BaseModel):
    """Standard error response."""

    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional details")

class FeedbackRequest(BaseModel):
    session_id: str
    relevant_docs: List[str] = []  # IDs de documentos relevantes
    non_relevant_docs: List[str] = []  # IDs de documentos no relevantes
    original_query: str | None = None  
    top_k: int = 5  # Número de documentos para la nueva búsqueda
    class Config:
        extra = "allow"
        arbitrary_types_allowed = True


class FeedbackResponse(BaseModel):
    answer: str
    retrieved_docs: List[Dict[str, Any]]
    reformulated_query: Dict[str, float]  # Términos con sus pesos
    session_id: str
