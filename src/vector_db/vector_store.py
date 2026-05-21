from __future__ import annotations

import json
from typing import Any
import numpy as np
from tqdm import tqdm

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from src.config import VECTOR_DB_COLLECTION_NAME, VECTOR_DB_PERSIST_DIR, VECTOR_DB_TOP_K
from src.errors.vector_db_errors import VectorStoreOperationError
from src.utils.logger import vector_logger as logger


class VectorStore:
    """
    Vector database using Chroma DB via LangChain.
    """

    COLLECTION_NAME = VECTOR_DB_COLLECTION_NAME

    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings
        self._persist_dir = VECTOR_DB_PERSIST_DIR

        self._vectorstore = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=self._embeddings,
            persist_directory=self._persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )

    def setup(
            self,
            doc_ids: list[str],
            texts: list[str],
            metadatas: list[dict],
            reset: bool = True,
            batch_size: int = 5000,
        ) -> None:
            """
            Initialise the store with documents. Uses batching with tqdm.
            """
            try:
                if reset:
                    self._vectorstore.delete_collection()
                    self._vectorstore = Chroma(
                        collection_name=self.COLLECTION_NAME,
                        embedding_function=self._embeddings,
                        persist_directory=self._persist_dir,
                        collection_metadata={"hnsw:space": "cosine"},
                    )

                logger.info(f"Adding {len(doc_ids)} documents to Chroma in batches...")

                # Clean metadata using numpy
                clean_metadatas = np.array([self._clean_metadata(m) for m in metadatas], dtype=object)

                # Convert to numpy for efficient slicing
                doc_ids_arr = np.array(doc_ids, dtype=object)
                texts_arr = np.array(texts, dtype=object)

                total = len(doc_ids)
                num_batches = int(np.ceil(total / batch_size))

                # Use tqdm for progress
                pbar = tqdm(total=total, desc="Adding to Chroma", unit="docs")
                
                for batch_idx in range(num_batches):
                    start = batch_idx * batch_size
                    end = min(start + batch_size, total)
                    
                    batch_ids = doc_ids_arr[start:end].tolist()
                    batch_texts = texts_arr[start:end].tolist()
                    batch_metadatas = clean_metadatas[start:end].tolist()
                    
                    self._vectorstore.add_texts(
                        texts=batch_texts,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                    )
                    
                    pbar.update(end - start)
                    pbar.set_postfix({"batch": f"{batch_idx + 1}/{num_batches}"})

                pbar.close()

                logger.info(
                    f"Initialised with {self.stats()['num_documents']} documents."
                )
            except Exception as exc:
                raise VectorStoreOperationError("Failed to setup vector store.") from exc

    async def add_documents(self, documents: list[Any], batch_size: int = 5000) -> None:
            """
            Add LangChain Document objects to the store. Uses numpy batching + tqdm.
            """
            try:
                logger.info(f"Adding {len(documents)} documents to Chroma in batches...")

                # Convert to numpy
                docs_arr = np.array(documents, dtype=object)
                total = len(documents)
                num_batches = int(np.ceil(total / batch_size))

                pbar = tqdm(total=total, desc="Adding to Chroma", unit="docs")
                
                for batch_idx in range(num_batches):
                    start = batch_idx * batch_size
                    end = min(start + batch_size, total)
                    batch = docs_arr[start:end].tolist()
                    
                    # Clean metadata in batch
                    for doc in batch:
                        doc.metadata = self._clean_metadata(doc.metadata)

                    self._vectorstore.add_documents(batch)
                    
                    pbar.update(end - start)
                    pbar.set_postfix({"batch": f"{batch_idx + 1}/{num_batches}"})

                pbar.close()
                
                logger.info(f"Total documents: {self.stats()['num_documents']}")
            except Exception as exc:
                raise VectorStoreOperationError("Failed to add documents.") from exc

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
            """
            Rank documents by similarity.
            """
            if top_k is None:
                top_k = VECTOR_DB_TOP_K
            try:
                results = self._vectorstore.similarity_search_with_relevance_scores(
                    query,
                    k=top_k,
                )

                output = []
                for i, (doc, score) in enumerate(results, start=1):
                    metadata = doc.metadata
                    output.append(
                        {
                            "rank": i,
                            "doc_id": doc.id
                            if hasattr(doc, "id")
                            else metadata.get("url", ""),
                            "score": round(score, 6),
                            "title": metadata.get("title", ""),
                            "url": metadata.get("url", ""),
                            "source": metadata.get("source", ""),
                            "content_preview": doc.page_content[:200] + "...",
                            "metadata": metadata,
                        }
                    )

                return output
            except Exception as exc:
                raise VectorStoreOperationError("Vector search failed.") from exc

    def as_retriever(self, **kwargs):
            """Return the LangChain retriever interface."""
            return self._vectorstore.as_retriever(**kwargs)

    def stats(self) -> dict:
            # Chroma LangChain doesn't expose count directly easily without accessing _collection
            try:
                count = self._vectorstore._collection.count()
                return {
                    "num_documents": count,
                    "collection_name": self.COLLECTION_NAME,
                }
            except Exception as exc:
                raise VectorStoreOperationError("Failed to read vector store stats.") from exc

    @staticmethod
    def _clean_metadata(metadata: dict) -> dict:
            """Convert metadata to Chroma-compatible scalar values."""
            clean = {}
            for key, value in metadata.items():
                if value is None:
                    clean[key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    clean[key] = value
                elif isinstance(value, list):
                    clean[key] = ", ".join(str(v) for v in value)
                elif isinstance(value, dict):
                    clean[key] = json.dumps(value, ensure_ascii=False)
                else:
                    clean[key] = str(value)
            return clean

    def __repr__(self) -> str:
            return f"VectorStore(Chroma LC: {self.COLLECTION_NAME})"
