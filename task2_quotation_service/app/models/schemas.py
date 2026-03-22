"""
Pydantic models for the Quotation Microservice.
Covers request validation and structured response shapes.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


# ── Request models ────────────────────────────────────────────────────────────

class QuoteLineItem(BaseModel):
    product_sku: str = Field(..., min_length=2, max_length=50, examples=["LED-PANEL-60W"])
    quantity: int = Field(..., ge=1, le=100_000, examples=[500])
    requested_unit_price: Optional[float] = Field(
        None, ge=0, description="Optional override; pricing engine is used if omitted"
    )

    @field_validator("product_sku")
    @classmethod
    def sku_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class QuoteRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=200, examples=["Acme Lighting LLC"])
    customer_email: str = Field(..., examples=["buyer@acme.com"])
    customer_country: str = Field(default="AE", max_length=2, examples=["AE"])
    currency: str = Field(default="USD", max_length=3, examples=["USD"])
    line_items: List[QuoteLineItem] = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)
    validity_days: int = Field(default=30, ge=1, le=365)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


# ── Response models ───────────────────────────────────────────────────────────

class QuoteLineResult(BaseModel):
    product_sku: str
    product_name: str
    quantity: int
    unit_price: float
    discount_pct: float
    line_total: float
    currency: str


class QuoteSummary(BaseModel):
    subtotal: float
    discount_amount: float
    tax_amount: float
    tax_rate: float
    total: float
    currency: str


class QuoteResponse(BaseModel):
    quote_id: str = Field(default_factory=lambda: f"QT-{uuid.uuid4().hex[:8].upper()}")
    customer_name: str
    customer_email: str
    customer_country: str
    line_items: List[QuoteLineResult]
    summary: QuoteSummary
    valid_until: date = Field(
        default_factory=lambda: date.today() + timedelta(days=30)
    )
    notes: Optional[str] = None
    generated_at: str = Field(
        default_factory=lambda: date.today().isoformat()
    )
    terms: str = "Payment: 30% advance, 70% before shipment. Prices subject to change after validity date."

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "QT-A1B2C3D4",
                "customer_name": "Acme Lighting LLC",
                "customer_email": "buyer@acme.com",
                "customer_country": "AE",
                "line_items": [
                    {
                        "product_sku": "LED-PANEL-60W",
                        "product_name": "LED Panel Light 60W",
                        "quantity": 500,
                        "unit_price": 12.50,
                        "discount_pct": 5.0,
                        "line_total": 5937.50,
                        "currency": "USD",
                    }
                ],
                "summary": {
                    "subtotal": 5937.50,
                    "discount_amount": 312.50,
                    "tax_amount": 281.25,
                    "tax_rate": 0.05,
                    "total": 5906.25,
                    "currency": "USD",
                },
                "valid_until": "2025-07-31",
                "notes": None,
                "generated_at": "2025-06-30",
            }
        }


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    field: Optional[str] = None
