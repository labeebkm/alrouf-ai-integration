"""
RAG Query Engine (Task 3)
Combines retrieval + LLM synthesis with:
- Citation of source documents
- Bilingual support (EN / AR)
- Clear refusal when the answer is out of scope
- Latency + cost tracking
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

from retriever import Retriever, RetrievedChunk

logger = logging.getLogger(__name__)

# Score threshold below which we consider the query out-of-scope
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.05"))

# Domain keywords — at least one must appear in the query for it to be in-scope
_DOMAIN_KEYWORDS_EN = {
    "led", "light", "lighting", "watt", "lumen", "warranty", "payment", "shipping",
    "lead time", "panel", "street", "high bay", "tube", "downlight", "sku", "product",
    "order", "quote", "quotation", "rfq", "price", "certif", "install", "dim", "cri",
    "ip rating", "incoterm", "fob", "alrouf", "al rouf", "delivery", "moq", "sample",
    "distributor", "oem", "voltage", "driver", "beam", "efficacy",
}

_DOMAIN_KEYWORDS_AR = {
    "إضاءة", "led", "ضمان", "شحن", "دفع", "سعر", "منتج", "طلب", "عرض", "توصيل",
    "ضوء", "لمبة", "مصباح", "فاتورة", "تسليم", "شهادة", "تركيب",
}


def _is_domain_relevant(query: str, language: str) -> bool:
    """Check that at least one domain keyword appears in the query."""
    q_lower = query.lower()
    keywords = _DOMAIN_KEYWORDS_AR if language == "ar" else _DOMAIN_KEYWORDS_EN
    return any(kw in q_lower for kw in keywords)

# ── Response model ────────────────────────────────────────────────────────────

@dataclass
class Citation:
    doc_name: str
    excerpt:  str
    score:    float


@dataclass
class RAGResponse:
    query:         str
    answer:        str
    language:      str        # "en" or "ar"
    citations:     List[Citation]
    in_scope:      bool
    latency_ms:    float
    tokens_used:   int = 0
    estimated_cost_usd: float = 0.0
    model:         str = "mock"


# ── Mock LLM answer ───────────────────────────────────────────────────────────

_OUT_OF_SCOPE_EN = (
    "I'm sorry, but I can only answer questions about AL ROUF LED lighting products, "
    "pricing, warranties, shipping, and related policies. "
    "Your question appears to be outside my supported scope. "
    "Please contact sales@alrouf.com for further assistance."
)

_OUT_OF_SCOPE_AR = (
    "عذراً، يمكنني فقط الإجابة على الأسئلة المتعلقة بمنتجات إضاءة AL ROUF LED، "
    "والأسعار، والضمانات، والشحن، والسياسات ذات الصلة. "
    "يبدو أن سؤالك خارج نطاق دعمي. "
    "يرجى التواصل مع sales@alrouf.com للمساعدة."
)


def _mock_answer(query: str, chunks: List[RetrievedChunk], language: str) -> str:
    """
    Produce a template-based answer from top chunks without calling an LLM.
    Used in mock/offline mode.
    """
    if not chunks:
        return _OUT_OF_SCOPE_EN if language == "en" else _OUT_OF_SCOPE_AR

    context = "\n\n---\n\n".join(c.text[:400] for c in chunks[:3])

    if language == "ar":
        return (
            f"بناءً على وثائق منتجات AL ROUF:\n\n"
            f"{context[:600]}\n\n"
            f"[ملاحظة: هذه إجابة تجريبية من وضع المحاكاة — في الإنتاج سيتم استخدام نموذج اللغة الكامل]"
        )
    return (
        f"Based on AL ROUF product documentation:\n\n"
        f"{context[:600]}\n\n"
        f"[Note: This is a mock-mode template answer — a full LLM response is used in production]"
    )


# ── Language detection ────────────────────────────────────────────────────────

def _detect_language(text: str) -> str:
    """Heuristic: detect Arabic script presence."""
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    return "ar" if arabic_chars / max(len(text), 1) > 0.15 else "en"


# ── LLM synthesis ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a knowledgeable assistant for AL ROUF LED Lighting Technology Co. Ltd.
Answer questions ONLY based on the provided context documents.
If the answer is not in the context, say clearly that this is outside your supported scope.
Always cite the source document name when referencing specific facts.
Be concise, professional, and accurate.
If the user writes in Arabic, respond in Arabic.
If the user writes in English, respond in English."""


def _llm_answer(
    query: str,
    chunks: List[RetrievedChunk],
    language: str,
) -> tuple[str, int]:
    """Call OpenAI to synthesise an answer. Returns (answer, tokens_used)."""
    import openai
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model  = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[Source {i}: {chunk.doc_name}]\n{chunk.text}")
    context = "\n\n".join(context_parts)

    user_msg = f"Context:\n{context}\n\nQuestion: {query}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0,
        max_tokens=600,
    )
    answer = resp.choices[0].message.content.strip()
    tokens = resp.usage.total_tokens if resp.usage else 0
    return answer, tokens


def _estimate_cost(tokens: int, model: str) -> float:
    """Rough cost estimate based on public pricing (USD per 1M tokens)."""
    rates = {
        "gpt-4o-mini":    0.30,
        "gpt-4o":         5.00,
        "gpt-4-turbo":   10.00,
    }
    rate = rates.get(model, 0.30)
    return round(tokens * rate / 1_000_000, 6)


# ── Public interface ───────────────────────────────────────────────────────────

class RAGEngine:
    def __init__(
        self,
        store_path: str = "./vector_store",
        mock: bool = True,
        top_k: int = 4,
    ):
        self._mock     = mock
        self._top_k    = top_k
        self._retriever = Retriever(store_path=store_path, mock=mock)
        self._model    = "mock" if mock else os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def query(self, question: str) -> RAGResponse:
        """
        Full RAG pipeline: embed query → retrieve → synthesise → return with citations.

        Refuses clearly when top-retrieved chunks score below RELEVANCE_THRESHOLD.
        """
        t0 = time.perf_counter()
        language = _detect_language(question)

        # Retrieve
        chunks = self._retriever.search(question, top_k=self._top_k)

        # Scope guard: must pass BOTH similarity threshold AND domain keyword check
        top_score = chunks[0].score if chunks else 0.0
        in_scope = (top_score >= RELEVANCE_THRESHOLD) and _is_domain_relevant(question, language)

        if not in_scope:
            answer = _OUT_OF_SCOPE_EN if language == "en" else _OUT_OF_SCOPE_AR
            tokens, cost = 0, 0.0
        elif self._mock:
            answer = _mock_answer(question, chunks, language)
            tokens, cost = 0, 0.0
        else:
            answer, tokens = _llm_answer(question, chunks, language)
            cost = _estimate_cost(tokens, self._model)

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        citations = [
            Citation(
                doc_name=c.doc_name,
                excerpt=c.text[:150].replace("\n", " "),
                score=c.score,
            )
            for c in chunks[:3]
        ] if in_scope else []

        logger.info(
            "RAG query (%s) | lang=%s in_scope=%s top_score=%.4f latency=%.0fms tokens=%d cost=$%.6f",
            self._model, language, in_scope, top_score, latency_ms, tokens, cost,
        )

        return RAGResponse(
            query=question,
            answer=answer,
            language=language,
            citations=citations,
            in_scope=in_scope,
            latency_ms=latency_ms,
            tokens_used=tokens,
            estimated_cost_usd=cost,
            model=self._model,
        )
