"""
Bilingual Reply Generator
Produces a professional RFQ acknowledgement in both English and Arabic.
Uses a template engine with Groq LLM enhancement in live mode.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BilingualReply:
    english: str
    arabic: str
    subject_en: str
    subject_ar: str


# ── English template (fallback) ───────────────────────────────────────────────

_EN_TEMPLATE = """Dear {name},

Thank you for reaching out to AL ROUF LED Lighting Technology Co. Ltd.

We have successfully received your Request for Quotation{subject_clause} and have created a record in our system (Reference: {deal_id}).

Our sales team will review your requirements and prepare a detailed quotation within 1–2 business days.

Summary of your enquiry:
{items_summary}
{delivery_clause}
Should you have any questions in the meantime, please do not hesitate to contact us.

Best regards,
AL ROUF LED Lighting Technology Co. Ltd.
Sales & Quotation Team
"""

# ── Arabic template (fallback) ────────────────────────────────────────────────

_AR_TEMPLATE = """عزيزي/عزيزتي {name}،

شكراً لتواصلكم مع شركة الروف لتكنولوجيا إضاءة LED.

لقد استلمنا بنجاح طلب عرض الأسعار الخاص بكم{subject_clause_ar} وقمنا بتسجيله في نظامنا (المرجع: {deal_id}).

سيقوم فريق المبيعات لدينا بمراجعة متطلباتكم وإعداد عرض أسعار تفصيلي خلال 1-2 يوم عمل.

ملخص استفساركم:
{items_summary}
{delivery_clause_ar}
إذا كان لديكم أي استفسارات في الوقت الحالي، فلا تترددوا في التواصل معنا.

مع أطيب التحيات،
شركة الروف لتكنولوجيا إضاءة LED
فريق المبيعات وعروض الأسعار
"""


def _build_items_summary(line_items: list) -> str:
    if not line_items:
        return "  • (No line items parsed — please see attached enquiry)"
    lines = []
    for item in line_items[:10]:  # cap at 10 for email brevity
        qty = f" × {item.quantity}" if item.quantity else ""
        unit = f" {item.unit}" if item.unit else ""
        lines.append(f"  • {item.product_description}{qty}{unit}")
    return "\n".join(lines)


def generate_reply(
    rfq,
    deal_id: str,
    mock_mode: bool = True,
    use_llm: bool = False,
) -> BilingualReply:
    """
    Generate a bilingual acknowledgement reply for an inbound RFQ.

    Args:
        rfq:        ExtractedRFQ instance.
        deal_id:    CRM deal/reference ID to include in reply.
        mock_mode:  Skip LLM calls — use templates only.
        use_llm:    Use Groq to generate a personalised reply.

    Returns:
        BilingualReply with english and arabic fields.
    """
    name = rfq.sender_name or rfq.sender_company or "Valued Customer"
    items_summary = _build_items_summary(rfq.line_items)

    subject_clause = f" regarding '{rfq.subject}'" if rfq.subject else ""
    subject_clause_ar = f" بخصوص '{rfq.subject}'" if rfq.subject else ""

    delivery_clause = (
        f"\nRequested delivery: {rfq.delivery_date}\n" if rfq.delivery_date else ""
    )
    delivery_clause_ar = (
        f"\nتاريخ التسليم المطلوب: {rfq.delivery_date}\n" if rfq.delivery_date else ""
    )

    # Build template fallback versions
    english = _EN_TEMPLATE.format(
        name=name,
        subject_clause=subject_clause,
        deal_id=deal_id,
        items_summary=items_summary,
        delivery_clause=delivery_clause,
    ).strip()

    arabic = _AR_TEMPLATE.format(
        name=name,
        subject_clause_ar=subject_clause_ar,
        deal_id=deal_id,
        items_summary=items_summary,
        delivery_clause_ar=delivery_clause_ar,
    ).strip()

    subject_en = f"RE: Your RFQ – Reference {deal_id} | AL ROUF LED"
    subject_ar = f"RE: طلب عرض الأسعار – مرجع {deal_id} | الروف LED"

    # Enhance with Groq in live mode
    if use_llm and not mock_mode:
        english, arabic = _llm_enhance_reply(rfq, english, arabic, deal_id)

    logger.info("Bilingual reply generated for deal %s", deal_id)
    return BilingualReply(
        english=english,
        arabic=arabic,
        subject_en=subject_en,
        subject_ar=subject_ar,
    )


def _llm_enhance_reply(rfq, en_draft: str, ar_draft: str, deal_id: str):
    """Generate a polished bilingual reply using Groq llama-3.1-8b-instant."""
    try:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        items_text = "\n".join(
            f"- {li.product_description} x {li.quantity or '?'} {li.unit or 'units'}"
            for li in rfq.line_items[:8]
        ) or "- (see enquiry details)"

        prompt = f"""You are a professional sales correspondent for AL ROUF LED Lighting Technology Co. Ltd., a Chinese LED manufacturer.

Write a warm, professional RFQ acknowledgement email in BOTH English and Arabic.
Return ONLY a JSON object with exactly two keys: "english" and "arabic".
No markdown, no code fences, no extra explanation — just the raw JSON.

Context:
- Customer name: {rfq.sender_name or 'Valued Customer'}
- Company: {rfq.sender_company or 'N/A'}
- Deal reference: {deal_id}
- Items requested:
{items_text}
- Delivery date requested: {rfq.delivery_date or 'not specified'}
- Destination: {rfq.destination_port or 'not specified'}
- Payment terms: {rfq.payment_terms or 'not specified'}

Requirements:
- Thank the customer for their enquiry
- Confirm receipt and mention deal reference {deal_id}
- List the requested items clearly with quantities
- Promise a detailed quotation within 1-2 business days
- Professional but warm tone
- Arabic version must be proper Modern Standard Arabic (فصحى), not transliteration
- Keep each version under 250 words
"""
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        content = resp.choices[0].message.content
        # Handle both string and pre-parsed dict responses
        if isinstance(content, dict):
            data = content
        else:
            import re as _re
            raw = content.strip()
            if "```" in raw:
                raw = _re.sub(r"```(?:json)?", "", raw).strip()
            data = json.loads(raw)
        # Extract english — handle flat string or nested dict with body key
        en_raw = data.get("english", "")
        if isinstance(en_raw, dict):
            en_result = str(en_raw.get("body", en_raw.get("content", str(en_raw)))).strip()
        else:
            en_result = str(en_raw).strip()

        # Extract arabic — same handling
        ar_raw = data.get("arabic", "")
        if isinstance(ar_raw, dict):
            ar_result = str(ar_raw.get("body", ar_raw.get("content", str(ar_raw)))).strip()
        else:
            ar_result = str(ar_raw).strip()

        # Only use LLM result if it returned meaningful content
        if len(en_result) > 50 and len(ar_result) > 50:
            logger.info("Groq bilingual reply generated successfully")
            return en_result, ar_result
        else:
            logger.warning("Groq reply too short, falling back to template")
            return en_draft, ar_draft

    except Exception as exc:
        logger.warning("Groq reply generation failed, using template: %s", exc)
        return en_draft, ar_draft
