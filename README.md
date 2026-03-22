# AL ROUF AI Integration Engineer – Assessment Solution

**Candidate:** Labeeb K M  
**Role:** AI Integration Engineer  
**Company:** AL ROUF LED Lighting Technology Co. Ltd.

---

## Repository Structure

```
alrouf-ai-integration/
├── task1_rfq_crm/          # RFQ → CRM Automation workflow
├── task2_quotation_service/ # FastAPI Quotation Microservice
├── task3_rag_workflow/      # Bilingual RAG Knowledge Workflow
├── docs/                    # Architecture diagrams, notes
├── scripts/                 # Helper/setup scripts
├── .env.example             # Environment variable template
└── README.md                # This file
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- An OpenAI API key (or use offline mocks — see each task's README)

### 1. Clone & configure environment

```bash
git clone <your-repo-url>
cd alrouf-ai-integration
cp .env.example .env
# Edit .env and fill in your API keys
```

---

## Task 1 – RFQ → CRM Automation

A workflow that ingests an inbound RFQ email/message, extracts structured fields, creates a CRM record (HubSpot or mock), archives attachments, generates a bilingual (English + Arabic) reply draft, and triggers an internal Slack/email alert.

**Stack:** Python · Make.com (or n8n self-hosted) · HubSpot CRM API (mock fallback)

```bash
cd task1_rfq_crm
pip install -r requirements.txt
python rfq_processor.py --mock   # Run with mock CRM + mock email
```

See [`task1_rfq_crm/README.md`](task1_rfq_crm/README.md) for full details.

---

## Task 2 – Quotation Microservice

A FastAPI microservice that accepts product/quantity inputs and returns a structured quotation, with full OpenAPI docs, Docker packaging, and test coverage.

```bash
cd task2_quotation_service
# Option A: Docker (recommended)
docker-compose up --build
# Option B: Local
pip install -r requirements.txt
uvicorn app.main:app --reload
# Run tests
pytest tests/ -v
```

OpenAPI docs available at: `http://localhost:8000/docs`

See [`task2_quotation_service/README.md`](task2_quotation_service/README.md).

---

## Task 3 – Bilingual RAG Knowledge Workflow

A retrieval-augmented generation workflow over 3–5 sample LED lighting product documents. Supports English and Arabic queries, returns citations, and cleanly refuses out-of-scope questions.

```bash
cd task3_rag_workflow
pip install -r requirements.txt
python ingest.py          # Index documents
python query.py --mock    # Run sample queries (mock LLM mode)
pytest tests/ -v
```

See [`task3_rag_workflow/README.md`](task3_rag_workflow/README.md).

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI key for LLM calls | Optional (mock fallback) |
| `HUBSPOT_API_KEY` | HubSpot CRM API key | Optional (mock fallback) |
| `SLACK_WEBHOOK_URL` | Slack webhook for alerts | Optional (mock fallback) |
| `MOCK_MODE` | Set to `true` to run fully offline | No (default: false) |

---

## Architecture Overview

See [`docs/architecture.md`](docs/architecture.md) for full diagrams and decision notes.

Key design decisions:
- **Mock-first design:** Every external dependency has a mock fallback so the project runs offline.
- **Separation of concerns:** Each task is independently runnable.
- **Error handling:** All API calls wrapped with retry logic and structured error responses.
- **Security:** No secrets in code; all via `.env`. Input validation on all endpoints.

---

## AI Assistance Disclosure

Per assessment requirements — AI assistance (Claude) was used for:
- Boilerplate scaffolding of FastAPI app structure
- Initial prompt templates for bilingual reply generation
- Test case generation assistance

Personally implemented by candidate:
- All business logic, field extraction, and routing decisions
- CRM integration and mock design
- RAG chunking strategy and citation logic
- Docker configuration and CI setup
- Architecture decisions and trade-off analysis
