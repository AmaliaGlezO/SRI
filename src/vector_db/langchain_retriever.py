from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

class LangChainVectorRetriever(BaseRetriever):
    """
    A LangChain wrapper for the Chroma vector store that includes relevance scores.
    """
    vectorstore: Chroma
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        # Use similarity_search_with_relevance_scores to get scores
        results = self.vectorstore.similarity_search_with_relevance_scores(query, k=self.k)
        
        documents = []
        for doc, score in results:
            # Ensure score is in metadata
            doc.metadata["score"] = score
            documents.append(doc)
        
        return documents
