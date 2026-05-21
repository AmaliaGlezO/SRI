"""Pydantic models for API request/response schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a retrieved document."""

    doc_id: str
    title: str
    url: str
    source: str
    score: Optional[float] = None


class RetrievedDocument(BaseModel):
    """A document retrieved during search."""

    title: str
    url: str
    source: str
    score: Optional[float] = None
    content_preview: Optional[str] = None


class SourceInfo(BaseModel):
    """Information about a source used in answer generation."""

    title: str
    url: str
    source: str


class QueryRequest(BaseModel):
    """Request model for a query."""

    query: str = Field(..., description="User query in Spanish")
    use_rag: bool = Field(default=True, description="Whether to use the configurable RAG flow")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of documents to retrieve")
    temperature: Optional[float] = Field(default=None, description="LLM temperature")
    relevance_threshold: Optional[float] = Field(default=None, description="RAG relevance threshold")
    max_doc_chars: Optional[int] = Field(default=None, description="Max characters per document")
    use_prf: bool = Field(default=True, description="Whether to use Pseudo-Relevance Feedback")
    use_internet_search: bool = Field(
        default=True,
        description="Whether to allow internet search fallback when local relevance is low",
    )


class TokenUsage(BaseModel):
    """Token usage information."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class QueryResponse(BaseModel):
    """Response model for a query."""

    query: str = Field(description="Original user query")
    answer: str = Field(description="Generated answer")
    sources: List[SourceInfo] = Field(description="Sources used in the answer")
    search_performed: bool = Field(
        description="Whether internet search was performed as fallback"
    )
    top_local_score: float = Field(description="Relevance score of top local result")
    token_usage: TokenUsage = Field(default_factory=TokenUsage, description="Token usage for this query")
    retrieved_documents: List[RetrievedDocument] = Field(
        description="Documents retrieved and used"
    )
    status: List[str] = Field(
        default_factory=list,
        description="Pipeline steps performed during query processing"
    )




class IndexingRequest(BaseModel):
    """Request to rebuild or update the index."""

    force: bool = Field(default=False, description="Force rebuild even if index exists")


class IndexingResponse(BaseModel):
    """Response from indexing operation."""

    status: str = Field(description="Status of indexing operation")
    num_documents: int = Field(description="Total documents indexed")
    vocabulary_size: int = Field(description="Vocabulary size")
    message: str = Field(description="Human-readable message")




class IndexStats(BaseModel):
    """Statistics for an index."""

    num_documents: int
    vocabulary_size: int


class VectorStoreStats(BaseModel):
    """Statistics for the vector store."""

    num_documents: int
    collection_name: str


class SystemStatusResponse(BaseModel):
    """Response with system status information."""

    status: str = Field(description="Overall system status (healthy, degraded, error)")
    lm_retriever_available: bool
    vector_store_available: bool
    lm_stats: Optional[IndexStats] = None
    vector_stats: Optional[VectorStoreStats] = None
    model_info: Optional[str] = Field(default=None, description="Active LLM model information")
    message: str = Field(description="Additional status message")




class ErrorResponse(BaseModel):
    """Standard error response."""

    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional details")



class HealthCheckResponse(BaseModel):
    """Response from health check endpoint."""

    status: str = Field(description="Health status")
    version: str = Field(description="API version")
