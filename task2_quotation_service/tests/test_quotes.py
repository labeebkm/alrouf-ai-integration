"""
Tests for AL ROUF Quotation Microservice.
Covers: pricing engine, quote generation, API endpoints, edge cases.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pricing import PricingEngine, MOCK_CATALOGUE
from app.services.quote_service import QuoteService
from app.models.schemas import QuoteRequest, QuoteLineItem

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def pricing_engine():
    return PricingEngine(price_list_path="nonexistent.json")  # forces mock catalogue


@pytest.fixture
def quote_service():
    return QuoteService()


@pytest.fixture
def valid_quote_payload():
    return {
        "customer_name": "Test Company LLC",
        "customer_email": "test@example.com",
        "customer_country": "AE",
        "currency": "USD",
        "line_items": [
            {"product_sku": "LED-PANEL-60W", "quantity": 500},
        ],
        "validity_days": 30,
    }


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_root_returns_service_info(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


# ── Pricing Engine ────────────────────────────────────────────────────────────

class TestPricingEngine:
    def test_known_skus_loaded(self, pricing_engine):
        skus = pricing_engine.known_skus()
        assert len(skus) >= 5
        assert "LED-PANEL-60W" in skus

    def test_base_price_small_qty(self, pricing_engine):
        _, price, discount = pricing_engine.resolve("LED-PANEL-60W", 1)
        assert price == MOCK_CATALOGUE["LED-PANEL-60W"]["base_price"]
        assert discount == 0.0

    def test_tiered_price_500(self, pricing_engine):
        _, price, _ = pricing_engine.resolve("LED-PANEL-60W", 500)
        assert price == 12.00

    def test_tiered_price_1000(self, pricing_engine):
        _, price, _ = pricing_engine.resolve("LED-PANEL-60W", 1000)
        assert price == 10.50

    def test_volume_discount_applied_at_1000(self, pricing_engine):
        _, _, discount = pricing_engine.resolve("LED-PANEL-60W", 1000)
        assert discount == 1.5

    def test_volume_discount_at_10000(self, pricing_engine):
        _, _, discount = pricing_engine.resolve("LED-PANEL-60W", 10000)
        assert discount == 5.0

    def test_override_price_respected(self, pricing_engine):
        _, price, discount = pricing_engine.resolve("LED-PANEL-60W", 500, override_price=9.99)
        assert price == 9.99
        assert discount == 0.0

    def test_unknown_sku_raises(self, pricing_engine):
        with pytest.raises(ValueError, match="Unknown product SKU"):
            pricing_engine.resolve("NONEXISTENT-SKU", 10)

    def test_sku_case_insensitive_via_validator(self):
        req = QuoteLineItem(product_sku="led-panel-60w", quantity=10)
        assert req.product_sku == "LED-PANEL-60W"


# ── Quote Service ─────────────────────────────────────────────────────────────

class TestQuoteService:
    def test_generate_basic_quote(self, quote_service):
        req = QuoteRequest(
            customer_name="ACME Corp",
            customer_email="acme@test.com",
            line_items=[QuoteLineItem(product_sku="LED-PANEL-60W", quantity=100)],
        )
        quote = quote_service.generate(req)
        assert quote.quote_id.startswith("QT-")
        assert len(quote.line_items) == 1
        assert quote.summary.total > 0

    def test_tax_applied(self, quote_service):
        req = QuoteRequest(
            customer_name="Tax Test",
            customer_email="tax@test.com",
            line_items=[QuoteLineItem(product_sku="LED-TUBE-18W", quantity=1000)],
        )
        quote = quote_service.generate(req)
        expected_tax = round(quote.summary.subtotal * 0.05, 2)
        assert abs(quote.summary.tax_amount - expected_tax) < 0.01

    def test_multiline_quote(self, quote_service):
        req = QuoteRequest(
            customer_name="Multi Line",
            customer_email="multi@test.com",
            line_items=[
                QuoteLineItem(product_sku="LED-PANEL-60W", quantity=200),
                QuoteLineItem(product_sku="LED-STREET-100W", quantity=50),
            ],
        )
        quote = quote_service.generate(req)
        assert len(quote.line_items) == 2
        assert quote.summary.subtotal == sum(li.line_total for li in quote.line_items)

    def test_unknown_sku_raises(self, quote_service):
        req = QuoteRequest(
            customer_name="Bad SKU",
            customer_email="bad@test.com",
            line_items=[QuoteLineItem(product_sku="FAKE-SKU-999", quantity=10)],
        )
        with pytest.raises(ValueError, match="Unknown SKU"):
            quote_service.generate(req)

    def test_validity_date_respected(self, quote_service):
        from datetime import date, timedelta
        req = QuoteRequest(
            customer_name="Validity Test",
            customer_email="v@test.com",
            line_items=[QuoteLineItem(product_sku="LED-DOWNLIGHT-12W", quantity=100)],
            validity_days=45,
        )
        quote = quote_service.generate(req)
        expected = date.today() + timedelta(days=45)
        assert quote.valid_until == expected


# ── API Endpoints ─────────────────────────────────────────────────────────────

class TestQuoteAPI:
    def test_create_quote_201(self, valid_quote_payload):
        resp = client.post("/quotes/", json=valid_quote_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["quote_id"].startswith("QT-")
        assert data["customer_email"] == "test@example.com"
        assert data["summary"]["total"] > 0

    def test_create_quote_multiple_lines(self):
        payload = {
            "customer_name": "BigBuyer Ltd",
            "customer_email": "big@buyer.com",
            "currency": "USD",
            "line_items": [
                {"product_sku": "LED-PANEL-60W", "quantity": 1000},
                {"product_sku": "LED-TUBE-18W", "quantity": 5000},
                {"product_sku": "LED-HIGHBAY-150W", "quantity": 200},
            ],
        }
        resp = client.post("/quotes/", json=payload)
        assert resp.status_code == 201
        assert len(resp.json()["line_items"]) == 3

    def test_unknown_sku_returns_400(self, valid_quote_payload):
        valid_quote_payload["line_items"][0]["product_sku"] = "FAKE-SKU"
        resp = client.post("/quotes/", json=valid_quote_payload)
        assert resp.status_code == 400
        assert "Unknown SKU" in resp.json()["detail"]

    def test_invalid_email_returns_422(self, valid_quote_payload):
        valid_quote_payload["customer_email"] = "not-an-email"
        resp = client.post("/quotes/", json=valid_quote_payload)
        assert resp.status_code == 422

    def test_zero_quantity_returns_422(self, valid_quote_payload):
        valid_quote_payload["line_items"][0]["quantity"] = 0
        resp = client.post("/quotes/", json=valid_quote_payload)
        assert resp.status_code == 422

    def test_empty_line_items_returns_422(self, valid_quote_payload):
        valid_quote_payload["line_items"] = []
        resp = client.post("/quotes/", json=valid_quote_payload)
        assert resp.status_code == 422

    def test_list_skus(self):
        resp = client.get("/quotes/skus")
        assert resp.status_code == 200
        skus = resp.json()
        assert isinstance(skus, list)
        assert len(skus) >= 5

    def test_openapi_schema_accessible(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "AL ROUF Quotation Microservice"
