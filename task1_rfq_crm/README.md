# Task 1 — RFQ → CRM Automation

Full pipeline: extract RFQ fields → create CRM record → archive attachments → generate bilingual reply → send internal alert.

## Quick Start (mock mode — no API keys needed)

```bash
pip install -r requirements.txt
python rfq_processor.py --mock
```

## With custom RFQ input

```bash
python rfq_processor.py --mock --input my_rfq.txt --output ./output
```

## Live mode (requires .env with API keys)

```bash
python rfq_processor.py --live --llm
```

## Run Tests

```bash
pytest tests/ -v
```

## Pipeline Steps

1. **Extract** — regex extracts: email, name, company, phone, line items, delivery date, destination, payment terms
2. **CRM** — creates HubSpot Contact + Deal (or mock equivalent)
3. **Archive** — saves attachments to `./attachments/{deal_id}/` (or S3)
4. **Reply** — bilingual English + Arabic acknowledgement draft
5. **Alert** — Slack webhook + email notification to sales team

## Output Files

After running, `./output/` contains:
- `{DEAL_ID}_result.json` — full structured pipeline output
- `{DEAL_ID}_reply_EN.txt` — English reply draft
- `{DEAL_ID}_reply_AR.txt` — Arabic reply draft
