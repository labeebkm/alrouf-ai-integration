# Task 3 — Bilingual RAG Knowledge Workflow

Retrieval-augmented generation over AL ROUF LED product documentation.
Supports English and Arabic queries, returns citations, refuses out-of-scope questions.

## Quick Start (offline mock mode)

```bash
pip install -r requirements.txt
python query.py --mock
```

This ingests the 3 knowledge-base documents and runs 9 sample queries (EN + AR + out-of-scope).

## Step by Step

```bash
# 1. Ingest documents into vector store
python ingest.py --mock

# 2. Run a single query
python query.py --mock --question "What is the warranty on LED street lights?"

# 3. Run all sample queries
python query.py --mock

# 4. Run tests
pytest tests/ -v
```

## Live Mode (requires OPENAI_API_KEY)

```bash
python query.py --live --question "ما هي فترة الضمان لإضاءة الشوارع؟"
```

## Knowledge Base Documents

| File | Contents |
|------|----------|
| `doc1_panel_street_specs.txt` | LED Panel 60W + Street Light 100W specs |
| `doc2_warranty_shipping.txt` | Warranty policy + lead times + shipping terms |
| `doc3_highbay_pricing_faq.txt` | High Bay 150W specs + pricing/payment FAQ |

## Scope Refusal

Queries with no LED/lighting domain keywords are refused with a bilingual message.
Example refused queries: "capital of France", "write me a poem", geography questions.

## Latency & Cost

| Mode | Latency | Cost/query |
|------|---------|------------|
| Mock (offline) | <1ms | $0.00 |
| Live (gpt-4o-mini) | 700–1,800ms | ~$0.0003–$0.001 |

See `docs/architecture.md` for full details.
