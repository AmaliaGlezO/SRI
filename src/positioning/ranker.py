
from typing import Any, List

class ResultRanker:
    """
    Ranks retrieval results by sorting them from highest to lowest score.
    """
        
    def rank(
        self,
        results: List[Any],
    ) -> List[Any]:
        """Rank results by relevance score descending."""
        if not results:
            return results
        
        scored_results = []
        for doc in results:
            score = doc.metadata.get("score", 0.0) if doc.metadata else 0.0
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata["final_score"] = score
            scored_results.append((score, doc))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_results]
    
    def __str__(self) -> str:
        return "ResultRanker()"