"""
Document Ingestion Pipeline (Task 3)
Loads knowledge-base text files, chunks them, generates embeddings,
and saves to a local vector store (JSON-based mock or ChromaDB).

Usage:
    python ingest.py                    # uses ./docs/knowledge_base, saves to ./vector_store
    python ingest.py --mock             # uses mock embeddings (no API key needed)
    python ingest.py --docs /path/docs  # custom docs directory
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


@dataclass
class Chunk:
    chunk_id:  str
    doc_name:  str
    text:      str
    char_start: int
    embedding: List[float]


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, doc_name: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Chunk]:
    """Split text into overlapping chunks with unique IDs."""
    # Prefer splitting at paragraph boundaries
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: List[Chunk] = []
    current = ""
    current_start = 0
    pos = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 1 > size and current:
            chunk_id = hashlib.md5(f"{doc_name}:{current_start}".encode()).hexdigest()[:12]
            chunks.append(Chunk(
                chunk_id=chunk_id, doc_name=doc_name,
                text=current.strip(), char_start=current_start, embedding=[],
            ))
            # Keep overlap
            words = current.split()
            overlap_text = " ".join(words[-max(1, overlap // 6):])
            current_start = pos
            current = overlap_text + "\n\n" + para
        else:
            current = (current + "\n\n" + para).strip() if current else para
        pos += len(para) + 2

    if current.strip():
        chunk_id = hashlib.md5(f"{doc_name}:{current_start}".encode()).hexdigest()[:12]
        chunks.append(Chunk(
            chunk_id=chunk_id, doc_name=doc_name,
            text=current.strip(), char_start=current_start, embedding=[],
        ))

    logger.info("  %s → %d chunk(s)", doc_name, len(chunks))
    return chunks


# ── Embeddings ────────────────────────────────────────────────────────────────

def _mock_embedding(text: str, dim: int = 64) -> List[float]:
    """Deterministic mock embedding using character frequencies."""
    vec = [0.0] * dim
    for i, c in enumerate(text):
        vec[ord(c) % dim] += 1.0
    # Normalise
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


def embed_chunks(chunks: List[Chunk], mock: bool = True) -> List[Chunk]:
    """Generate embeddings for all chunks."""
    if mock:
        for chunk in chunks:
            chunk.embedding = _mock_embedding(chunk.text)
        logger.info("Mock embeddings generated for %d chunks", len(chunks))
        return chunks

    # Real sentence-transformers embeddings (runs locally, no API cost)
    from sentence_transformers import SentenceTransformer
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    logger.info("Loading sentence-transformer model: %s", model_name)
    model = SentenceTransformer(model_name)

    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb.tolist()

    logger.info("sentence-transformers embeddings generated for %d chunks (model=%s, dim=%d)",
                len(chunks), model_name, len(chunks[0].embedding))
    return chunks


# ── Vector store (JSON file-based) ───────────────────────────────────────────

def save_vector_store(chunks: List[Chunk], store_path: str) -> None:
    Path(store_path).mkdir(parents=True, exist_ok=True)
    index_path = Path(store_path) / "index.json"
    data = [asdict(c) for c in chunks]
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Vector store saved: %s (%d chunks)", index_path, len(chunks))


def load_vector_store(store_path: str) -> List[Chunk]:
    index_path = Path(store_path) / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Vector store not found at {index_path}. Run ingest.py first.")
    with open(index_path) as f:
        data = json.load(f)
    chunks = [Chunk(**d) for d in data]
    logger.info("Vector store loaded: %d chunks", len(chunks))
    return chunks


# ── Main ingestion ────────────────────────────────────────────────────────────

def ingest(docs_path: str, store_path: str, mock: bool = True) -> int:
    """
    Load all .txt/.md documents, chunk, embed, and save vector store.
    Returns the number of chunks indexed.
    """
    doc_dir = Path(docs_path)
    if not doc_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_path}")

    files = sorted(doc_dir.glob("*.txt")) + sorted(doc_dir.glob("*.md"))
    if not files:
        raise ValueError(f"No .txt or .md files found in {docs_path}")

    all_chunks: List[Chunk] = []
    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        chunks = chunk_text(text, doc_name=fpath.name)
        all_chunks.extend(chunks)

    logger.info("Total chunks to embed: %d", len(all_chunks))
    all_chunks = embed_chunks(all_chunks, mock=mock)
    save_vector_store(all_chunks, store_path)

    # Save metadata summary
    meta = {
        "doc_count": len(files),
        "chunk_count": len(all_chunks),
        "embedding_dim": len(all_chunks[0].embedding) if all_chunks else 0,
        "mock_embeddings": mock,
        "documents": [f.name for f in files],
    }
    with open(Path(store_path) / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    logger.info("Ingestion complete. %d docs → %d chunks", len(files), len(all_chunks))
    return len(all_chunks)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument("--docs",  default="./docs/knowledge_base",  help="Docs directory")
    parser.add_argument("--store", default="./vector_store",          help="Vector store path")
    parser.add_argument("--mock",  action="store_true", default=True, help="Use mock embeddings")
    parser.add_argument("--live",  action="store_true",               help="Use real OpenAI embeddings")
    args = parser.parse_args()
    use_mock = not args.live
    n = ingest(args.docs, args.store, mock=use_mock)
    print(f"✓ Indexed {n} chunks into {args.store}")
