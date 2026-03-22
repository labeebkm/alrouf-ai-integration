"""
Quotation API router.
POST /quotes/         – generate a new quotation
GET  /quotes/skus     – list available product SKUs
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import QuoteRequest, QuoteResponse, ErrorResponse
from app.services.quote_service import QuoteService

logger = logging.getLogger(__name__)
router = APIRouter()

_quote_service = QuoteService()


@router.post(
    "/",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new quotation",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        400: {"model": ErrorResponse, "description": "Business logic error (e.g. unknown SKU)"},
    },
)
async def create_quote(request: QuoteRequest) -> QuoteResponse:
    """
    Accepts an RFQ-style payload with one or more line items and returns
    a fully priced quotation with tiered pricing, discounts, and VAT applied.

    **Offline/mock mode:** Works without any API keys — uses built-in price catalogue.
    """
    try:
        quote = _quote_service.generate(request)
        logger.info(
            "Quote %s generated for %s (%d lines, total %s %s)",
            quote.quote_id,
            request.customer_email,
            len(quote.line_items),
            quote.summary.total,
            quote.summary.currency,
        )
        return quote
    except ValueError as exc:
        logger.warning("Quote generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error generating quote: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


@router.get(
    "/skus",
    summary="List available product SKUs",
    response_model=list[str],
)
async def list_skus() -> list[str]:
    """Returns all product SKUs currently available for quotation."""
    return _quote_service.known_skus()
