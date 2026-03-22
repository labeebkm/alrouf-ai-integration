# AL ROUF AI Integration Engineer – Assessment Solution

**Candidate:** Labeeb K M  
**Role:** AI Integration Engineer  
**Company:** AL ROUF LED Lighting Technology Co. Ltd.

---

## Repository Structure

```
alrouf-ai-integration/
├── task1_rfq_crm/           # RFQ → CRM Automation pipeline
├── task2_quotation_service/  # FastAPI Quotation Microservice
├── task3_rag_workflow/       # Bilingual RAG Knowledge Workflow
├── docs/                     # Architecture documentation
├── scripts/                  # Setup and PDF generation scripts
├── .env.example              # Environment variable template
└── README.md                 # This file
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- A Groq API key for live mode — free at [console.groq.com](https://console.groq.com)
- All tasks run fully offline in mock mode — no API keys needed

### Setup

```bash
git clone <your-repo-url>
cd alrouf-ai-integration
cp .env.example .env
# Edit .env and add your GROQ_API_KEY for live mode
```

---

## Task 1 – RFQ → CRM Automation

Processes an inbound RFQ email through a 5-stage pipeline: field extraction → CRM record → attachment archive → bilingual reply → internal alert.

**Stack:** Python · Groq `llama-3.1-8b-instant` · HubSpot CRM API (mock fallback)

```bash
cd task1_rfq_crm
pip install -r requirements.txt

# Offline mock mode (no API key needed)
python rfq_processor.py --mock

# Live mode with real Groq LLM
python task1_demo_live.py

# Tests
pytest tests/ -v   # 23 tests
```

See [`task1_rfq_crm/README.md`](task1_rfq_crm/README.md) for full details.

---

## Task 2 – Quotation Microservice

FastAPI microservice that accepts RFQ-style line items and returns structured quotations with tiered pricing, volume discounts, and VAT.

**Stack:** Python · FastAPI · Pydantic v2 · Docker

```bash
cd task2_quotation_service

# Option A: Docker (recommended)
docker-compose up --build

# Option B: Local
pip install -r requirements.txt
uvicorn app.main:app --reload

# Tests
pytest tests/ -v   # 24 tests
```

OpenAPI docs: `http://localhost:8000/docs`

See [`task2_quotation_service/README.md`](task2_quotation_service/README.md).

---

## Task 3 – Bilingual RAG Knowledge Workflow

Retrieval-augmented generation over 3 AL ROUF LED product documents. Supports English and Arabic queries, returns source citations, and refuses out-of-scope questions in the query language.

**Stack:** Python · `sentence-transformers` (paraphrase-multilingual-MiniLM-L12-v2) · Groq `llama-3.1-8b-instant` · JSON vector store

```bash
cd task3_rag_workflow
pip install -r requirements.txt

# Offline mock mode (no API key needed)
python query.py --mock

# Live mode with real embeddings + Groq LLM
python task3_demo_live.py

# Tests
pytest tests/ -v   # 26 tests
```

See [`task3_rag_workflow/README.md`](task3_rag_workflow/README.md).

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for LLM calls (Tasks 1 & 3) | Optional (mock fallback) |
| `GROQ_MODEL` | Groq model name | No (default: `llama-3.1-8b-instant`) |
| `EMBEDDING_MODEL` | sentence-transformers model name | No (default: `paraphrase-multilingual-MiniLM-L12-v2`) |
| `HUBSPOT_API_KEY` | HubSpot CRM API key | Optional (mock fallback) |
| `SLACK_WEBHOOK_URL` | Slack webhook for internal alerts | Optional (mock fallback) |
| `MOCK_MODE` | Set to `true` to run fully offline | No (default: `false`) |

---

## Test Results

All tasks run in offline mock mode — no API keys needed for tests:

```bash
# Task 1
cd task1_rfq_crm && pytest tests/ -v       # 23 passed

# Task 2
cd task2_quotation_service && pytest tests/ -v  # 24 passed

# Task 3
cd task3_rag_workflow && pytest tests/ -v  # 26 passed

# Total: 73 / 73 passed
```

---

## Architecture Overview

See [`docs/architecture.md`](docs/architecture.md) for full design notes and trade-off analysis.

Key design decisions:
- **Mock-first design:** Every external dependency has a mock fallback — project runs fully offline.
- **Groq over OpenAI:** Free tier, faster inference, OpenAI-compatible API. No cost for development.
- **sentence-transformers locally:** Embeddings run on-device — zero API cost, no rate limits, works offline after first download.
- **Separation of concerns:** Each task is independently runnable with its own requirements.txt.
- **Security:** No secrets in code — all via `.env`. Input validation on all API endpoints.

---

## AI Assistance Disclosure

Per assessment requirements — full transparency on AI tool usage:

| Area | AI Used For | Candidate's Own Work |
|---|---|---|
| Task 1 | Claude for initial module scaffolding | All regex patterns, Groq integration, pipeline orchestration, error handling |
| Task 2 | Claude for FastAPI boilerplate | Pricing tier algorithm, all business rules, Docker config, all 24 tests |
| Task 3 | Claude for chunking structure suggestion | Embedding design, cosine similarity retriever, scope guard, bilingual detection, all 26 tests |
| Groq integration | None — fully candidate implemented | Groq API wiring for Tasks 1 & 3, prompt engineering, response parsing |
