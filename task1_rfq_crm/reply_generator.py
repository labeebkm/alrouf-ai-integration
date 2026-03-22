"""
Bilingual Reply Generator
Produces a professional RFQ acknowledgement in both English and Arabic.
Uses a template engine with optional LLM enhancement.
"""
from __future__ import annotations

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


# ── English template ──────────────────────────────────────────────────────────

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

# ── Arabic template ───────────────────────────────────────────────────────────

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
        lines.append(f"  • {item.product_description}{qty}")
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
        mock_mode:  Skip LLM calls.
        use_llm:    Use OpenAI to generate a more personalised reply.

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
    """Optionally polish the reply using OpenAI."""
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        prompt = f"""Refine this customer RFQ acknowledgement email to sound more professional and warm.
Keep it concise. Return JSON with keys "english" and "arabic".

English draft:
{en_draft}

Arabic draft:
{ar_draft}

Context: B2B LED lighting manufacturer replying to an inbound quotation request.
Deal reference: {deal_id}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
        )
        import json
        data = json.loads(resp.choices[0].message.content)
        return data.get("english", en_draft), data.get("arabic", ar_draft)
    except Exception as exc:
        logger.warning("LLM reply enhancement failed: %s", exc)
        return en_draft, ar_draft
