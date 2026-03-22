"""
RFQ Field Extractor
Parses an inbound RFQ message (email body or plain text) and extracts
structured fields using regex + heuristics, with Groq LLM enhancement.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RFQLineItem:
    product_description: str
    quantity: Optional[int] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ExtractedRFQ:
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    sender_company: Optional[str] = None
    sender_phone: Optional[str] = None
    sender_country: Optional[str] = None
    subject: Optional[str] = None
    delivery_date: Optional[str] = None
    destination_port: Optional[str] = None
    payment_terms: Optional[str] = None
    line_items: List[RFQLineItem] = field(default_factory=list)
    raw_notes: Optional[str] = None
    extraction_method: str = "regex"
    confidence: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ── Regex patterns ────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", re.I)
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,20}\d)")
_QTY_RE   = re.compile(
    r"(\d[\d,]*)\s*(?:x\s*)?(?:pcs?|units?|sets?|pieces?|nos?\.?|qty\.?)?",
    re.I
)
_DATE_RE  = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{2}[/-]\d{2}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{1,2},?\s*\d{4})\b",
    re.I
)
_COMPANY_KEYWORDS = ["ltd", "llc", "inc", "co.", "corp", "trading", "group", "company"]


def _extract_email(text: str) -> Optional[str]:
    m = _EMAIL_RE.search(text)
    return m.group(0).lower() if m else None


def _extract_phone(text: str) -> Optional[str]:
    m = _PHONE_RE.search(text)
    return m.group(1).strip() if m else None


def _extract_company(text: str) -> Optional[str]:
    """Find company name: prefer explicit 'Company:' label, then keyword heuristic."""
    # 1. Explicit label
    m = re.search(r"(?:company|organization|org|firm)\s*[:\-]\s*(.+)", text, re.I)
    if m:
        return m.group(1).strip()[:120]
    # 2. Look for short lines containing company keywords (< 80 chars to avoid paragraphs)
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 80:
            continue
        line_lower = line.lower()
        if any(kw in line_lower for kw in _COMPANY_KEYWORDS):
            cleaned = re.sub(r"^(from|name|contact)\s*[:\-]?\s*", "", line, flags=re.I)
            return cleaned.strip()
    return None


def _extract_name(text: str) -> Optional[str]:
    """Look for lines starting with 'Name:', 'From:', 'Contact:' etc."""
    patterns = [
        r"(?:name|contact|from|sender)\s*[:\-]\s*(.+)",
        r"^(?:dear\s+)?(?:mr\.?|ms\.?|mrs\.?)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I | re.M)
        if m:
            return m.group(1).strip()
    return None


def _extract_delivery_date(text: str) -> Optional[str]:
    m = _DATE_RE.search(text)
    return m.group(0) if m else None


def _extract_destination(text: str) -> Optional[str]:
    m = re.search(r"(?:destination|port|deliver\s+to|ship\s+to)\s*[:\-]?\s*(.+)", text, re.I)
    return m.group(1).strip() if m else None


def _extract_payment_terms(text: str) -> Optional[str]:
    m = re.search(r"(?:payment|terms|t\/t|l\/c|lc)\s*[:\-]?\s*(.+)", text, re.I)
    return m.group(1).strip()[:100] if m else None


def _extract_line_items(text: str) -> List[RFQLineItem]:
    """
    Heuristic line-item extraction.
    Looks for lines that contain a quantity and a product description.
    """
    items: List[RFQLineItem] = []
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        qty_match = _QTY_RE.search(line)
        if not qty_match:
            continue
        # Must look like it mentions a product (has letters around the qty)
        if not re.search(r"[A-Za-z]{3,}", line):
            continue
        # Skip lines that are clearly metadata
        if re.match(r"(?:name|email|phone|from|date|subject)\s*:", line, re.I):
            continue

        raw_qty = qty_match.group(1).replace(",", "")
        try:
            qty = int(raw_qty)
        except ValueError:
            qty = None

        # Product description: everything except the qty token
        desc = _QTY_RE.sub("", line).strip(" -•:,")
        if len(desc) < 3:
            continue

        items.append(RFQLineItem(product_description=desc, quantity=qty))

    return items


def _compute_confidence(rfq: ExtractedRFQ) -> float:
    """Simple confidence scoring based on how many key fields were found."""
    score = 0.0
    if rfq.sender_email:     score += 0.25
    if rfq.sender_name:      score += 0.10
    if rfq.sender_company:   score += 0.10
    if rfq.line_items:       score += 0.35
    if rfq.delivery_date:    score += 0.10
    if rfq.destination_port: score += 0.10
    return round(min(score, 1.0), 2)


# ── Public interface ──────────────────────────────────────────────────────────

def extract_rfq(
    message_body: str,
    subject: str = "",
    use_llm: bool = False,
    mock_mode: bool = True,
) -> ExtractedRFQ:
    """
    Extract structured fields from a raw RFQ message.

    Args:
        message_body: Raw email/message body text.
        subject:      Email subject line (optional).
        use_llm:      If True and GROQ_API_KEY is set, use Groq LLM for extraction.
        mock_mode:    Skip LLM calls entirely (for offline/testing).

    Returns:
        ExtractedRFQ dataclass with all discovered fields.
    """
    rfq = ExtractedRFQ(subject=subject or None)

    rfq.sender_email     = _extract_email(message_body)
    rfq.sender_name      = _extract_name(message_body)
    rfq.sender_company   = _extract_company(message_body)
    rfq.sender_phone     = _extract_phone(message_body)
    rfq.delivery_date    = _extract_delivery_date(message_body)
    rfq.destination_port = _extract_destination(message_body)
    rfq.payment_terms    = _extract_payment_terms(message_body)
    rfq.line_items       = _extract_line_items(message_body)
    rfq.raw_notes        = message_body[:500]
    rfq.extraction_method = "regex"

    # Enhance with Groq LLM when in live mode
    if use_llm and not mock_mode:
        rfq = _llm_enhance(rfq, message_body)

    rfq.confidence = _compute_confidence(rfq)
    logger.info(
        "RFQ extracted: email=%s company=%s items=%d confidence=%.2f method=%s",
        rfq.sender_email, rfq.sender_company,
        len(rfq.line_items), rfq.confidence, rfq.extraction_method,
    )
    return rfq


def _llm_enhance(rfq: ExtractedRFQ, raw_text: str) -> ExtractedRFQ:
    """
    Use Groq (llama-3.1-8b-instant) to accurately extract all fields.
    Always overrides line items with LLM results (more accurate than regex).
    Falls back to regex results if API call fails.
    """
    try:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        prompt = f"""Extract the following fields from this RFQ (Request for Quotation) message as JSON.
Return ONLY valid JSON with no markdown, no code fences, no explanation.

Fields to extract:
- sender_name (full name as string, or null)
- sender_email (email address as string, or null)
- sender_company (company name only, short form, or null)
- sender_phone (phone number as string, or null)
- sender_country (country name or code, or null)
- delivery_date (date as string, or null)
- destination_port (port/city/country for delivery as string, or null)
- payment_terms (payment method and terms as string, or null)
- line_items: array of objects, each with:
    - product_description: full product name including wattage e.g. "LED Street Light 100W"
    - quantity: integer number of units, or null
    - unit: unit of measure e.g. "pcs", "units", or null

Important: For line_items, include the complete product description with wattage/model.

RFQ Message:
{raw_text[:3000]}
"""
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1000,
        )
        raw_json = resp.choices[0].message.content.strip()
        # Strip markdown fences if model adds them despite instructions
        raw_json = raw_json.strip("```json").strip("```").strip()
        data = json.loads(raw_json)

        # Always fill scalar fields that regex missed
        for key in ["sender_name", "sender_email", "sender_company",
                    "sender_phone", "sender_country", "delivery_date",
                    "destination_port", "payment_terms"]:
            if not getattr(rfq, key) and data.get(key):
                setattr(rfq, key, data[key])

        # Always override line items with Groq results — more accurate than regex
        if data.get("line_items"):
            rfq.line_items = [
                RFQLineItem(
                    product_description=item.get("product_description", ""),
                    quantity=item.get("quantity"),
                    unit=item.get("unit"),
                )
                for item in data["line_items"]
                if item.get("product_description")
            ]

        rfq.extraction_method = "groq_llama3_enhanced"
        logger.info("Groq extraction successful: %d line items extracted", len(rfq.line_items))

    except Exception as exc:
        logger.warning("Groq enhancement failed, using regex results: %s", exc)

    return rfq
