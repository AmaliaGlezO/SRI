from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from src.retrieval.lm_retriever import LMRetriever


class LangChainLMRetriever(BaseRetriever):
    """
    A LangChain wrapper for the custom LMRetriever.
    """

    retriever: LMRetriever
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        # Use the underlying LMRetriever to get results
        results = self.retriever.retrieve(query, top_k=self.k)

        documents = []
        for res in results:
            # Convert dict results to LangChain Document objects
            score = res.get("score", 0.0)
            doc = Document(
                page_content=res.get("content_preview", ""),
                metadata={
                    "doc_id": res.get("doc_id"),
                    "title": res.get("title"),
                    "url": res.get("url"),
                    "score": res.get("score"),
                    "rank": res.get("rank"),
                },
            )
            doc.metadata["score"] = max(0.0, min(1.0, float(score)))
            documents.append(doc)

        return documents
