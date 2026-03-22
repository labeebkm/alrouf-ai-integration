"""
Quote generation service.
Orchestrates pricing, discount, tax, and response assembly.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List

from app.models.schemas import (
    QuoteLineItem,
    QuoteLineResult,
    QuoteRequest,
    QuoteResponse,
    QuoteSummary,
)
from app.services.pricing import PricingEngine
from app.core.config import settings

logger = logging.getLogger(__name__)


class QuoteService:
    def __init__(self):
        self._pricing = PricingEngine(settings.price_list_path)

    def generate(self, request: QuoteRequest) -> QuoteResponse:
        """
        Main entry point: validate line items, resolve prices,
        compute totals, and return a structured QuoteResponse.
        """
        line_results: List[QuoteLineResult] = []
        unknown_skus: List[str] = []

        for item in request.line_items:
            try:
                product_name, unit_price, discount_pct = self._pricing.resolve(
                    sku=item.product_sku,
                    quantity=item.quantity,
                    override_price=item.requested_unit_price,
                )
            except ValueError:
                unknown_skus.append(item.product_sku)
                continue

            discounted_price = unit_price * (1 - discount_pct / 100)
            line_total = round(discounted_price * item.quantity, 2)

            line_results.append(
                QuoteLineResult(
                    product_sku=item.product_sku,
                    product_name=product_name,
                    quantity=item.quantity,
                    unit_price=round(unit_price, 4),
                    discount_pct=discount_pct,
                    line_total=line_total,
                    currency=request.currency,
                )
            )

        if unknown_skus:
            raise ValueError(f"Unknown SKU(s): {', '.join(unknown_skus)}")

        if not line_results:
            raise ValueError("No valid line items to quote.")

        subtotal = sum(item.line_total for item in line_results)
        discount_amount = sum(
            lr.unit_price * lr.quantity * (lr.discount_pct / 100)
            for lr in line_results
        )
        tax_amount = round(subtotal * settings.tax_rate, 2)
        total = round(subtotal + tax_amount, 2)

        summary = QuoteSummary(
            subtotal=round(subtotal, 2),
            discount_amount=round(discount_amount, 2),
            tax_amount=tax_amount,
            tax_rate=settings.tax_rate,
            total=total,
            currency=request.currency,
        )

        valid_until = date.today() + timedelta(days=request.validity_days)

        return QuoteResponse(
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            customer_country=request.customer_country,
            line_items=line_results,
            summary=summary,
            valid_until=valid_until,
            notes=request.notes,
        )

    def known_skus(self) -> list[str]:
        return self._pricing.known_skus()
