# Architecture Documentation — AL ROUF AI Integration Assessment

## System Overview

Three independent, composable services share a common design philosophy:
- **Mock-first**: every external dependency has an in-process mock — the full project runs offline with zero API keys.
- **Fail-safe**: all external calls are wrapped in try/except with graceful degradation.
- **Separation of concerns**: each module has a single responsibility; orchestration lives in a thin runner layer.

---

## Task 1 – RFQ to CRM Automation

### Pipeline Flow
```
Inbound RFQ text  →  extractor.py  →  crm.py  →  archiver.py  →  reply_generator.py  →  notifier.py
```

**extractor.py**: Regex-based field extraction (email, company, phone, line items, delivery date, destination, payment terms). Optional OpenAI LLM enhancement when confidence is low.

**crm.py**: Creates HubSpot Contact + Deal via REST API. Falls back to an in-memory mock dict when HUBSPOT_API_KEY is absent.

**archiver.py**: Saves attachments to a deal-scoped folder on disk. Optional S3 upload. Sanitises filenames to prevent path traversal.

**reply_generator.py**: Produces bilingual (English + Arabic) acknowledgement from Jinja-style templates. Optional LLM polish via OpenAI.

**notifier.py**: Sends Slack webhook POST and SMTP email alert. Logs only in mock mode — no exception is raised on failure.

### Key Design Decisions
- Regex-first extraction keeps the pipeline fast and deterministic for 90%+ of structured B2B RFQs.
- Confidence scoring gives a quality signal so low-confidence RFQs can be flagged for human review.
- CRM/alert failures are isolated — they do not abort the pipeline.

---

## Task 2 – Quotation Microservice

### Request Flow
```
POST /quotes/  →  Pydantic validation  →  QuoteService  →  PricingEngine  →  QuoteResponse (201)
```

**PricingEngine**: Loads tiered pricing from `data/price_list.json`. Falls back to the built-in `MOCK_CATALOGUE` if the file is missing. Applies qty-breakpoint pricing then an additional volume discount tier.

**QuoteService**: Iterates line items, resolves prices, computes subtotal, applies 5% VAT, and assembles a `QuoteResponse` with a unique `QT-` prefixed ID.

### Container Design
Multi-stage Dockerfile: builder stage installs dependencies into `/install`; runtime stage is `python:3.11-slim` with a non-root user. HEALTHCHECK polls `/health` every 30 seconds.

### Error Handling
- Unknown SKU → HTTP 400 with SKU names listed.
- Validation errors → HTTP 422 with field-level Pydantic detail.
- Unexpected errors → HTTP 500 with sanitised message only (no stack traces).

---

## Task 3 – Bilingual RAG Workflow

### Query Flow
```
Query  →  Language detect  →  Embed query  →  Cosine similarity search  →  Scope guard  →  Synthesis  →  RAGResponse
```

**Ingestion**: Documents are paragraph-chunked (512 chars, 64 overlap) and embedded. Mock embeddings use a deterministic character-frequency vector (dim=64, L2-normalised). The vector store is a single `index.json` file — zero infrastructure dependency.

**Scope guard**: If the top retrieved chunk scores below `RELEVANCE_THRESHOLD` (0.05), the engine returns a refusal message in the same language as the query.

**Language**: Arabic script is detected by Unicode codepoint ratio. Arabic queries receive Arabic answers and Arabic refusals.

### Latency and Cost

| Mode | Embed | LLM | Cost/query |
|---|---|---|---|
| Mock (offline) | <1 ms | 0 ms | $0.00 |
| OpenAI small + gpt-4o-mini | ~100 ms | ~500 ms | ~$0.0001 |

At 1,000 queries/day with gpt-4o-mini the estimated cost is under $0.10/day.

### Key Design Decisions
- JSON vector store avoids ChromaDB/Pinecone operational overhead; swap is a one-line change in `Retriever.__init__`.
- Mock embeddings are deterministic so CI passes with zero API spend.
- Citations expose scores so the UI layer can threshold display (e.g. only show score > 0.7).

---

## Security Hygiene

| Concern | Mitigation |
|---|---|
| Secrets in code | All credentials via .env / env vars; .env in .gitignore |
| Input validation | Pydantic v2 strict validation on all API inputs |
| Path traversal | _sanitize_filename() strips directory components |
| Container privilege | Non-root user in Docker runtime stage |
| LLM prompt injection | System prompt enforces strict scope; retrieved context is pre-validated text |
| API error leakage | HTTP 500 returns sanitised message only; details stay in server logs |

---

## Trade-off Summary

| Decision | Alternative considered | Rationale |
|---|---|---|
| Regex extraction (T1) | LLM-only extraction | Faster, cheaper, deterministic; LLM available as opt-in |
| JSON vector store (T3) | ChromaDB / Pinecone | Zero infra dependency; swappable at retriever boundary |
| Mock embeddings in tests | Real embeddings | CI runs offline; deterministic = reproducible test results |
| FastAPI (T2) | Flask / Django | Native async, automatic OpenAPI, best-in-class Pydantic integration |
| HubSpot CRM (T1) | Salesforce / Pipedrive | Most common in LED/manufacturing SME segment; free tier available |
