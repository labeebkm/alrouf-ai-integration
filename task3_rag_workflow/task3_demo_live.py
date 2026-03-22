"""
Live Demo Script — Tests real Groq LLM + sentence-transformers embeddings
Run this AFTER setting GROQ_API_KEY in your .env file

Usage:
    cd task3_rag_workflow
    python demo_live.py
"""
import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")

def check_env():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your-groq" in key:
        print("ERROR: GROQ_API_KEY not set in .env file")
        print("Get your free key at: https://console.groq.com")
        sys.exit(1)
    print(f"✓ GROQ_API_KEY found (ending: ...{key[-6:]})")

def run_live_demo():
    check_env()

    from ingest import ingest
    from rag_engine import RAGEngine

    print("\n=== Step 1: Ingesting documents with sentence-transformers embeddings ===")
    n = ingest("./docs/knowledge_base", "./vector_store_live", mock=False)
    print(f"✓ Indexed {n} chunks with real embeddings (all-MiniLM-L6-v2)")

    print("\n=== Step 2: Running live queries with Groq llama-3.1-8b-instant ===\n")
    engine = RAGEngine(store_path="./vector_store_live", mock=False)

    questions = [
        "What is the warranty period for the LED Street Light 100W?",
        "What are the technical specifications of the LED Panel 60W?",
        "What payment terms are available for large orders?",
        "ما هي فترة الضمان لإضاءة الشوارع LED؟",
        "What is the capital of France?",  # should be refused
    ]

    for q in questions:
        print(f"Q: {q}")
        resp = engine.query(q)
        print(f"Lang: {resp.language.upper()} | In-scope: {resp.in_scope} | "
              f"Latency: {resp.latency_ms:.0f}ms | Tokens: {resp.tokens_used} | "
              f"Cost: ${resp.estimated_cost_usd:.6f}")
        print(f"A: {resp.answer[:400]}")
        if resp.citations:
            for c in resp.citations:
                print(f"  [{c.score:.3f}] {c.doc_name}")
        print("-" * 60)

if __name__ == "__main__":
    run_live_demo()
