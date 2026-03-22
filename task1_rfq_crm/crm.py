"""
CRM Integration Layer
Supports HubSpot (real) and an in-memory mock (for offline/testing).
Creates a Contact + Deal record from an ExtractedRFQ.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CRMResult:
    contact_id: str
    deal_id: str
    crm_url: Optional[str]
    mock: bool = False


# ── Mock CRM ──────────────────────────────────────────────────────────────────

_MOCK_DB: dict = {"contacts": {}, "deals": {}}


def _mock_create_contact(rfq) -> str:
    cid = f"MOCK-CONTACT-{uuid.uuid4().hex[:8].upper()}"
    _MOCK_DB["contacts"][cid] = {
        "id": cid,
        "email": rfq.sender_email,
        "name": rfq.sender_name,
        "company": rfq.sender_company,
        "phone": rfq.sender_phone,
        "country": rfq.sender_country,
        "created_at": datetime.utcnow().isoformat(),
    }
    logger.info("[MOCK CRM] Contact created: %s", cid)
    return cid


def _mock_create_deal(rfq, contact_id: str) -> str:
    did = f"MOCK-DEAL-{uuid.uuid4().hex[:8].upper()}"
    _MOCK_DB["deals"][did] = {
        "id": did,
        "contact_id": contact_id,
        "subject": rfq.subject or "Inbound RFQ",
        "company": rfq.sender_company,
        "line_items": [
            {"product": li.product_description, "quantity": li.quantity}
            for li in rfq.line_items
        ],
        "delivery_date": rfq.delivery_date,
        "destination": rfq.destination_port,
        "payment_terms": rfq.payment_terms,
        "stage": "rfq_received",
        "created_at": datetime.utcnow().isoformat(),
    }
    logger.info("[MOCK CRM] Deal created: %s", did)
    return did


# ── HubSpot CRM ───────────────────────────────────────────────────────────────

def _hubspot_create_contact(rfq, api_key: str) -> str:
    """Create or update a HubSpot contact. Returns the contact ID."""
    import urllib.request

    name_parts = (rfq.sender_name or "").split(maxsplit=1)
    payload = {
        "properties": {
            "email":       rfq.sender_email or "",
            "firstname":   name_parts[0] if name_parts else "",
            "lastname":    name_parts[1] if len(name_parts) > 1 else "",
            "company":     rfq.sender_company or "",
            "phone":       rfq.sender_phone or "",
            "country":     rfq.sender_country or "",
        }
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    contact_id = data["id"]
    logger.info("HubSpot contact created/updated: %s", contact_id)
    return contact_id


def _hubspot_create_deal(rfq, contact_id: str, api_key: str) -> str:
    """Create a HubSpot deal and associate it with the contact."""
    import urllib.request

    items_text = "\n".join(
        f"- {li.product_description} x {li.quantity or '?'}"
        for li in rfq.line_items
    )
    payload = {
        "properties": {
            "dealname":     f"RFQ – {rfq.sender_company or rfq.sender_email} – {datetime.utcnow().strftime('%Y-%m-%d')}",
            "pipeline":     os.getenv("HUBSPOT_PIPELINE_ID", "default"),
            "dealstage":    os.getenv("HUBSPOT_STAGE_ID", "appointmentscheduled"),
            "description":  f"Inbound RFQ\n\nItems:\n{items_text}\n\nDelivery: {rfq.delivery_date}\nDestination: {rfq.destination_port}\nPayment: {rfq.payment_terms}",
            "closedate":    "",
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
            }
        ],
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.hubapi.com/crm/v3/objects/deals",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    deal_id = data["id"]
    logger.info("HubSpot deal created: %s", deal_id)
    return deal_id


# ── Public interface ──────────────────────────────────────────────────────────

def create_crm_record(rfq, mock_mode: bool = True) -> CRMResult:
    """
    Create CRM contact + deal from extracted RFQ.
    Uses HubSpot if HUBSPOT_API_KEY is set and mock_mode=False,
    otherwise falls back to in-memory mock.
    """
    hubspot_key = os.getenv("HUBSPOT_API_KEY", "")

    if mock_mode or not hubspot_key:
        contact_id = _mock_create_contact(rfq)
        deal_id    = _mock_create_deal(rfq, contact_id)
        return CRMResult(
            contact_id=contact_id,
            deal_id=deal_id,
            crm_url=None,
            mock=True,
        )

    try:
        contact_id = _hubspot_create_contact(rfq, hubspot_key)
        deal_id    = _hubspot_create_deal(rfq, contact_id, hubspot_key)
        portal_id  = os.getenv("HUBSPOT_PORTAL_ID", "")
        crm_url    = f"https://app.hubspot.com/contacts/{portal_id}/deal/{deal_id}" if portal_id else None
        return CRMResult(
            contact_id=contact_id,
            deal_id=deal_id,
            crm_url=crm_url,
            mock=False,
        )
    except Exception as exc:
        logger.error("HubSpot API failed, falling back to mock: %s", exc)
        contact_id = _mock_create_contact(rfq)
        deal_id    = _mock_create_deal(rfq, contact_id)
        return CRMResult(contact_id=contact_id, deal_id=deal_id, crm_url=None, mock=True)
