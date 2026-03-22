# Task 2 — Quotation Microservice

FastAPI-based quotation microservice for AL ROUF LED products.

## Quick Start

### Option A — Docker (recommended)
```bash
docker-compose up --build
```
Service available at `http://localhost:8000`

### Option B — Local Python
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Tests
```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/quotes/skus` | List available SKUs |
| POST | `/quotes/` | Generate a quotation |

OpenAPI docs: `http://localhost:8000/docs`

## Sample Request

```bash
curl -X POST http://localhost:8000/quotes/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Acme Lighting LLC",
    "customer_email": "buyer@acme.com",
    "currency": "USD",
    "line_items": [
      {"product_sku": "LED-PANEL-60W", "quantity": 500},
      {"product_sku": "LED-STREET-100W", "quantity": 100}
    ],
    "validity_days": 30
  }'
```

## Available SKUs (mock catalogue)

| SKU | Product | Base Price |
|-----|---------|------------|
| LED-PANEL-60W | LED Panel Light 60W | $14.00 |
| LED-STREET-100W | LED Street Light 100W | $45.00 |
| LED-HIGHBAY-150W | LED High Bay Light 150W | $55.00 |
| LED-DOWNLIGHT-12W | LED Downlight 12W | $5.50 |
| LED-TUBE-18W | LED Tube Light T8 18W | $4.00 |

Pricing tiers and volume discounts applied automatically.
