from typing import List
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.documents import Document

from src.errors.internet_search_error import WebSearchExecutionError

class WebSearcher:
    """
    Search the internet using DuckDuckGo and return results as LangChain Documents.
    """
    def __init__(self, max_results: int = 5):
        self.search_wrapper = DuckDuckGoSearchAPIWrapper(
            region="es-es", time="y", max_results=max_results
        )

    def search(self, query: str) -> List[Document]:
        """
        Perform a search and return results as a list of Documents.
        """
        print(f"[WebSearcher] Searching the internet for: {query}")
        try:
            results = self.search_wrapper.results(query, max_results=5)
            documents = []
            for res in results:
                doc = Document(
                    page_content=res.get("snippet", ""),
                    metadata={
                        "title": res.get("title", "Internet Result"),
                        "url": res.get("link", ""),
                        "source": "Internet",
                    },
                )
                documents.append(doc)
            return documents
        except Exception as exc:
            raise WebSearchExecutionError("Error during web search execution.") from exc
