"""
RAG Retriever
Handles similarity search over the vector store using cosine similarity.
Supports English and Arabic queries (language-agnostic embedding lookup).
"""
from __future__ import annotations

import math
import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from ingest import Chunk, load_vector_store, _mock_embedding

logger = logging.getLogger(__name__)

TOP_K = int(os.getenv("TOP_K_RESULTS", "4"))


@dataclass
class RetrievedChunk:
    chunk_id:  str
    doc_name:  str
    text:      str
    score:     float


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    n_a  = math.sqrt(sum(x * x for x in a))
    n_b  = math.sqrt(sum(x * x for x in b))
    if n_a == 0 or n_b == 0:
        return 0.0
    return dot / (n_a * n_b)


def _embed_query(query: str, mock: bool = True) -> List[float]:
    if mock:
        return _mock_embedding(query)
    import openai
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model  = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    resp   = client.embeddings.create(model=model, input=[query])
    return resp.data[0].embedding


class Retriever:
    def __init__(self, store_path: str = "./vector_store", mock: bool = True):
        self._mock = mock
        self._chunks: List[Chunk] = load_vector_store(store_path)

    def search(self, query: str, top_k: int = TOP_K) -> List[RetrievedChunk]:
        """
        Find the top-k most relevant chunks for a query.
        Works for both English and Arabic queries.
        """
        q_emb = _embed_query(query, mock=self._mock)
        scored = [
            (c, _cosine_similarity(q_emb, c.embedding))
            for c in self._chunks
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        results = [
            RetrievedChunk(
                chunk_id=c.chunk_id,
                doc_name=c.doc_name,
                text=c.text,
                score=round(score, 4),
            )
            for c, score in scored[:top_k]
        ]
        logger.debug("Query '%s...' → top score=%.4f", query[:40], results[0].score if results else 0)
        return results
