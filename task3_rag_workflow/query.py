"""
RAG Query Runner (Task 3)
Run sample queries against the AL ROUF knowledge base.

Usage:
    python query.py --mock                         # offline mode
    python query.py --mock --question "warranty?"  # single question
    python query.py --live                         # uses OpenAI API
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s")

from ingest import ingest
from rag_engine import RAGEngine

SAMPLE_QUESTIONS = [
    # English
    "What is the warranty period for LED street lights?",
    "What are the technical specifications for the LED Panel 60W?",
    "What are the payment terms for large orders?",
    "What is the lead time for an order of 500 units?",
    "What certifications does the High Bay 150W have?",
    # Arabic
    "ما هي فترة الضمان لإضاءة الشوارع LED؟",
    "ما هي شروط الدفع للطلبات الكبيرة؟",
    # Out-of-scope
    "What is the capital of France?",
    "Can you write me a poem about the ocean?",
]


def run_queries(questions: list, mock: bool, store_path: str, output_file: str = None):
    engine = RAGEngine(store_path=store_path, mock=mock)
    results = []

    print("\n" + "="*70)
    print("AL ROUF RAG Knowledge Workflow — Query Results")
    print("="*70)

    for q in questions:
        resp = engine.query(q)
        results.append({
            "query":         resp.query,
            "language":      resp.language,
            "in_scope":      resp.in_scope,
            "answer":        resp.answer,
            "citations":     [{"doc": c.doc_name, "score": c.score, "excerpt": c.excerpt} for c in resp.citations],
            "latency_ms":    resp.latency_ms,
            "tokens_used":   resp.tokens_used,
            "cost_usd":      resp.estimated_cost_usd,
            "model":         resp.model,
        })

        print(f"\nQ [{resp.language.upper()}]: {resp.query}")
        print(f"In-scope: {resp.in_scope} | Latency: {resp.latency_ms:.0f}ms | Tokens: {resp.tokens_used} | Cost: ${resp.estimated_cost_usd:.6f}")
        print(f"A: {resp.answer[:300]}{'...' if len(resp.answer) > 300 else ''}")
        if resp.citations:
            print("Citations:")
            for c in resp.citations:
                print(f"  [{c.score:.4f}] {c.doc_name}: {c.excerpt[:80]}...")
        print("-"*70)

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")

    # Summary
    in_scope_count = sum(1 for r in results if r["in_scope"])
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    total_cost  = sum(r["cost_usd"] for r in results)
    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(results)} queries | {in_scope_count} in-scope | {len(results)-in_scope_count} refused")
    print(f"Avg latency: {avg_latency:.0f}ms | Total cost: ${total_cost:.6f}")
    print("="*70)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG queries over AL ROUF knowledge base")
    parser.add_argument("--mock",      action="store_true", default=True)
    parser.add_argument("--live",      action="store_true")
    parser.add_argument("--question",  type=str, default=None, help="Single question override")
    parser.add_argument("--docs",      default="./docs/knowledge_base")
    parser.add_argument("--store",     default="./vector_store")
    parser.add_argument("--output",    default="./output/rag_results.json")
    parser.add_argument("--no-ingest", action="store_true", help="Skip re-ingestion")
    args = parser.parse_args()

    use_mock = not args.live

    # Ingest if needed
    if not args.no_ingest:
        ingest(args.docs, args.store, mock=use_mock)

    questions = [args.question] if args.question else SAMPLE_QUESTIONS
    run_queries(questions, mock=use_mock, store_path=args.store, output_file=args.output)
