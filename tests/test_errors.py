"""Tests for error handling modules."""

import pytest
from src.errors.extract_data_errors import ExtractDataError, MissingSpiderNameError, HTMLParsingError
from src.errors.indexing_errors import IndexingError, DocumentIndexingError, IndexBuildError
from src.errors.rag_errors import RAGError, RAGRetrievalError, RAGAnswerGenerationError
from src.errors.vector_db_errors import VectorDBError, VectorStoreInitError, DocumentAddError
from src.errors.retrieval_errors import RetrievalError, QueryProcessingError, NoResultsError
from src.errors.llm_errors import LLMError, ModelLoadError, InferenceError
from src.errors.internet_search_error import InternetSearchError, WebSearchExecutionError


class TestExtractDataErrors:
    """Test ExtractDataError hierarchy."""

    def test_extract_data_error_base(self):
        """Test base ExtractDataError."""
        error = ExtractDataError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_missing_spider_name_error(self):
        """Test MissingSpiderNameError."""
        error = MissingSpiderNameError("spider not found")
        assert isinstance(error, ExtractDataError)
        assert str(error) == "spider not found"

    def test_html_parsing_error(self):
        """Test HTMLParsingError."""
        error = HTMLParsingError("parsing failed")
        assert isinstance(error, ExtractDataError)


class TestIndexingErrors:
    """Test IndexingError hierarchy."""

    def test_indexing_error_base(self):
        """Test base IndexingError."""
        error = IndexingError("Indexing failed")
        assert isinstance(error, Exception)

    def test_document_indexing_error(self):
        """Test DocumentIndexingError."""
        error = DocumentIndexingError("Document indexing failed")
        assert isinstance(error, IndexingError)

    def test_index_build_error(self):
        """Test IndexBuildError."""
        error = IndexBuildError("Index build failed")
        assert isinstance(error, IndexingError)


class TestRAGErrors:
    """Test RAGError hierarchy."""

    def test_rag_error_base(self):
        """Test base RAGError."""
        error = RAGError("RAG failed")
        assert isinstance(error, Exception)

    def test_rag_retrieval_error(self):
        """Test RAGRetrievalError."""
        error = RAGRetrievalError("Retrieval failed")
        assert isinstance(error, RAGError)

    def test_rag_answer_generation_error(self):
        """Test RAGAnswerGenerationError."""
        error = RAGAnswerGenerationError("Answer generation failed")
        assert isinstance(error, RAGError)


class TestVectorDBErrors:
    """Test VectorDBError hierarchy."""

    def test_vector_db_error_base(self):
        """Test base VectorDBError."""
        error = VectorDBError("VectorDB error")
        assert isinstance(error, Exception)

    def test_vector_store_init_error(self):
        """Test VectorStoreInitError."""
        error = VectorStoreInitError("Init failed")
        assert isinstance(error, VectorDBError)

    def test_document_add_error(self):
        """Test DocumentAddError."""
        error = DocumentAddError("Add failed")
        assert isinstance(error, VectorDBError)


class TestRetrievalErrors:
    """Test RetrievalError hierarchy."""

    def test_retrieval_error_base(self):
        """Test base RetrievalError."""
        error = RetrievalError("Retrieval error")
        assert isinstance(error, Exception)

    def test_query_processing_error(self):
        """Test QueryProcessingError."""
        error = QueryProcessingError("Query processing failed")
        assert isinstance(error, RetrievalError)

    def test_no_results_error(self):
        """Test NoResultsError."""
        error = NoResultsError("No results found")
        assert isinstance(error, RetrievalError)


class TestLLMErrors:
    """Test LLMError hierarchy."""

    def test_llm_error_base(self):
        """Test base LLMError."""
        error = LLMError("LLM error")
        assert isinstance(error, Exception)

    def test_model_load_error(self):
        """Test ModelLoadError."""
        error = ModelLoadError("Model load failed")
        assert isinstance(error, LLMError)

    def test_inference_error(self):
        """Test InferenceError."""
        error = InferenceError("Inference failed")
        assert isinstance(error, LLMError)


class TestInternetSearchErrors:
    """Test InternetSearchError hierarchy."""

    def test_internet_search_error_base(self):
        """Test base InternetSearchError."""
        error = InternetSearchError("Search error")
        assert isinstance(error, Exception)

    def test_web_search_execution_error(self):
        """Test WebSearchExecutionError."""
        error = WebSearchExecutionError("Search execution failed")
        assert isinstance(error, InternetSearchError)
