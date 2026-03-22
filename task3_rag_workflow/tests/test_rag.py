"""Tests for Task 3: RAG ingestion, retrieval, query engine."""
import math
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import chunk_text, embed_chunks, save_vector_store, load_vector_store, Chunk, _mock_embedding
from retriever import Retriever, _cosine_similarity
from rag_engine import RAGEngine, _detect_language, RELEVANCE_THRESHOLD


DOCS_PATH  = str(Path(__file__).parent.parent / "docs" / "knowledge_base")
SAMPLE_DOC = """
AL ROUF LED Panel Light 60W offers 6600 lumens and CRI >= 90.
It has a 5 year warranty.

Payment terms are 30% advance and 70% before shipment.

The lead time for 500 units is 25-30 business days.
"""


# ── Chunking tests ─────────────────────────────────────────────────────────────

class TestChunking:
    def test_chunks_created(self):
        chunks = chunk_text(SAMPLE_DOC, "test_doc.txt", size=200, overlap=20)
        assert len(chunks) >= 1

    def test_all_chunks_have_text(self):
        chunks = chunk_text(SAMPLE_DOC, "test.txt")
        for c in chunks:
            assert len(c.text) > 0

    def test_chunk_ids_unique(self):
        chunks = chunk_text(SAMPLE_DOC * 5, "test.txt", size=100, overlap=10)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_preserves_doc_name(self):
        chunks = chunk_text(SAMPLE_DOC, "my_doc.txt")
        assert all(c.doc_name == "my_doc.txt" for c in chunks)


# ── Embedding tests ────────────────────────────────────────────────────────────

class TestEmbedding:
    def test_mock_embedding_correct_dim(self):
        emb = _mock_embedding("hello world", dim=64)
        assert len(emb) == 64

    def test_mock_embedding_normalised(self):
        emb = _mock_embedding("test text here", dim=64)
        norm = math.sqrt(sum(x * x for x in emb))
        assert abs(norm - 1.0) < 1e-4

    def test_mock_embedding_deterministic(self):
        e1 = _mock_embedding("same text")
        e2 = _mock_embedding("same text")
        assert e1 == e2

    def test_different_texts_differ(self):
        e1 = _mock_embedding("LED panel specifications")
        e2 = _mock_embedding("shipping and warranty policy")
        sim = _cosine_similarity(e1, e2)
        assert sim < 1.0

    def test_embed_chunks_populates_embeddings(self):
        chunks = chunk_text(SAMPLE_DOC, "test.txt")
        chunks = embed_chunks(chunks, mock=True)
        for c in chunks:
            assert len(c.embedding) > 0


# ── Vector store tests ────────────────────────────────────────────────────────

class TestVectorStore:
    def test_save_and_load(self, tmp_path):
        chunks = chunk_text(SAMPLE_DOC, "test.txt")
        chunks = embed_chunks(chunks, mock=True)
        save_vector_store(chunks, str(tmp_path))
        loaded = load_vector_store(str(tmp_path))
        assert len(loaded) == len(chunks)
        assert loaded[0].chunk_id == chunks[0].chunk_id

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_vector_store(str(tmp_path / "nonexistent"))


# ── Retriever tests ────────────────────────────────────────────────────────────

class TestRetriever:
    @pytest.fixture(scope="class")
    def retriever(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("store")
        from ingest import ingest
        ingest(DOCS_PATH, str(tmp_path), mock=True)
        return Retriever(store_path=str(tmp_path), mock=True)

    def test_cosine_similarity_identical(self):
        v = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_search_returns_results(self, retriever):
        results = retriever.search("warranty period street light", top_k=3)
        assert len(results) <= 3
        assert all(r.score >= 0 for r in results)

    def test_search_scores_descending(self, retriever):
        results = retriever.search("LED panel specifications", top_k=4)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# ── Language detection ────────────────────────────────────────────────────────

class TestLanguageDetection:
    def test_english_detected(self):
        assert _detect_language("What is the warranty period?") == "en"

    def test_arabic_detected(self):
        assert _detect_language("ما هي فترة الضمان للمنتجات؟") == "ar"

    def test_mixed_defaults_to_english(self):
        # Mostly English with a few Arabic chars
        assert _detect_language("Warranty هي period") == "en"


# ── RAG Engine tests ───────────────────────────────────────────────────────────

class TestRAGEngine:
    @pytest.fixture(scope="class")
    def engine(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("rag_store")
        from ingest import ingest
        ingest(DOCS_PATH, str(tmp_path), mock=True)
        return RAGEngine(store_path=str(tmp_path), mock=True)

    def test_in_scope_query_returns_answer(self, engine):
        resp = engine.query("What is the warranty on the LED street light?")
        assert resp.in_scope is True
        assert len(resp.answer) > 10
        assert resp.latency_ms > 0

    def test_in_scope_query_has_citations(self, engine):
        resp = engine.query("LED panel 60W specifications")
        assert resp.in_scope is True
        assert len(resp.citations) >= 1
        for c in resp.citations:
            assert c.doc_name
            assert c.score >= 0

    def test_out_of_scope_query_refused(self, engine):
        resp = engine.query("What is the capital city of Australia?")
        assert resp.in_scope is False
        assert len(resp.citations) == 0
        assert "scope" in resp.answer.lower() or "sorry" in resp.answer.lower()

    def test_arabic_query_answered(self, engine):
        resp = engine.query("ما هي فترة الضمان لمنتجات LED؟")
        assert resp.language == "ar"
        assert resp.answer  # must produce something

    def test_out_of_scope_arabic_refused_in_arabic(self, engine):
        resp = engine.query("ما هو عاصمة اليابان؟")
        assert resp.in_scope is False
        # Should respond in Arabic
        has_arabic = any("\u0600" <= c <= "\u06ff" for c in resp.answer)
        assert has_arabic

    def test_mock_mode_zero_cost(self, engine):
        resp = engine.query("shipping lead time")
        assert resp.tokens_used == 0
        assert resp.estimated_cost_usd == 0.0

    def test_response_has_latency(self, engine):
        resp = engine.query("payment terms")
        assert resp.latency_ms >= 0

    def test_multiple_queries_consistent(self, engine):
        q = "warranty period for street lights"
        r1 = engine.query(q)
        r2 = engine.query(q)
        assert r1.in_scope == r2.in_scope
