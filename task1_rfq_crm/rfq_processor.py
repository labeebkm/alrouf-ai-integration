"""
RFQ Processor — Main Orchestrator (Task 1)

Full pipeline:
  1. Extract structured fields from inbound RFQ message
  2. Create CRM contact + deal record
  3. Archive attachments
  4. Generate bilingual client reply draft
  5. Trigger internal alert

Usage:
    python rfq_processor.py --mock
    python rfq_processor.py --input sample_rfq.txt
    python rfq_processor.py --help
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from extractor      import extract_rfq
from crm            import create_crm_record
from archiver       import archive_attachments
from reply_generator import generate_reply
from notifier       import send_internal_alert

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sample RFQ for demo / mock mode ──────────────────────────────────────────

SAMPLE_RFQ = """
From: Ahmed Al-Rashidi <ahmed@gulf-constructions.ae>
Subject: RFQ - LED Lighting for Warehouse Project

Dear Sales Team,

I am writing on behalf of Gulf Constructions LLC to request a quotation for the following LED lighting products for our upcoming warehouse project in Dubai.

Name: Ahmed Al-Rashidi
Company: Gulf Constructions LLC
Phone: +971 50 123 4567
Email: ahmed@gulf-constructions.ae

Required items:
- LED High Bay 150W × 200 pcs
- LED Panel 60W × 500 pcs
- LED Tube 18W × 1000 pcs
- LED Street Light 100W × 50 units

Destination port: Jebel Ali, Dubai, UAE
Required delivery date: 15/03/2025
Payment terms: 30% advance, 70% before shipment
Incoterms: FOB Shenzhen

Please include your best prices, lead time, and warranty terms.

Best regards,
Ahmed Al-Rashidi
Procurement Manager
Gulf Constructions LLC
"""


def run_pipeline(
    message_body: str,
    subject: str = "",
    attachments: list = None,
    mock_mode: bool = True,
    use_llm: bool = False,
    output_dir: str = "./output",
) -> dict:
    """
    Execute the full RFQ processing pipeline.
    Returns a summary dict with all results.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    attachments = attachments or []

    logger.info("=== RFQ Pipeline Start (mock=%s) ===", mock_mode)

    # Step 1: Extract structured fields
    logger.info("Step 1/5: Extracting RFQ fields...")
    rfq = extract_rfq(message_body, subject=subject, use_llm=use_llm, mock_mode=mock_mode)
    logger.info("  → email=%s, company=%s, items=%d, confidence=%.0f%%",
                rfq.sender_email, rfq.sender_company,
                len(rfq.line_items), rfq.confidence * 100)

    # Step 2: Create CRM record
    logger.info("Step 2/5: Creating CRM record...")
    crm_result = create_crm_record(rfq, mock_mode=mock_mode)
    logger.info("  → contact=%s deal=%s mock=%s",
                crm_result.contact_id, crm_result.deal_id, crm_result.mock)

    # Step 3: Archive attachments
    logger.info("Step 3/5: Archiving attachments (%d)...", len(attachments))
    storage_path = os.getenv("ATTACHMENT_STORAGE_PATH", f"{output_dir}/attachments")
    att_records = archive_attachments(
        attachments, crm_result.deal_id,
        storage_path=storage_path, mock_mode=mock_mode
    )
    logger.info("  → %d attachment(s) archived", len(att_records))

    # Step 4: Generate bilingual reply
    logger.info("Step 4/5: Generating bilingual reply draft...")
    reply = generate_reply(rfq, crm_result.deal_id, mock_mode=mock_mode, use_llm=use_llm)

    # Step 5: Send internal alert
    logger.info("Step 5/5: Sending internal alert...")
    alert = send_internal_alert(
        rfq, crm_result.deal_id, crm_url=crm_result.crm_url, mock_mode=mock_mode
    )
    logger.info("  → slack=%s email=%s", alert.slack_sent, alert.email_sent)

    # Assemble and save output
    result = {
        "pipeline_status": "success",
        "mock_mode": mock_mode,
        "rfq": rfq.to_dict(),
        "crm": {
            "contact_id": crm_result.contact_id,
            "deal_id": crm_result.deal_id,
            "crm_url": crm_result.crm_url,
            "mock": crm_result.mock,
        },
        "attachments": [
            {
                "filename": a.original_filename,
                "stored_path": a.stored_path,
                "size_bytes": a.size_bytes,
                "backend": a.storage_backend,
            }
            for a in att_records
        ],
        "reply_draft": {
            "subject_en": reply.subject_en,
            "subject_ar": reply.subject_ar,
            "english":    reply.english,
            "arabic":     reply.arabic,
        },
        "alert": {
            "slack_sent": alert.slack_sent,
            "email_sent": alert.email_sent,
        },
    }

    # Save outputs to disk
    out_path = Path(output_dir) / f"{crm_result.deal_id}_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    reply_en_path = Path(output_dir) / f"{crm_result.deal_id}_reply_EN.txt"
    reply_ar_path = Path(output_dir) / f"{crm_result.deal_id}_reply_AR.txt"
    reply_en_path.write_text(reply.english, encoding="utf-8")
    reply_ar_path.write_text(reply.arabic, encoding="utf-8")

    logger.info("=== Pipeline Complete. Output: %s ===", out_path)
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AL ROUF RFQ Processing Pipeline")
    parser.add_argument("--mock", action="store_true", default=True,
                        help="Run in mock mode (no external API calls)")
    parser.add_argument("--live", action="store_true",
                        help="Run in live mode (requires API keys in .env)")
    parser.add_argument("--llm", action="store_true",
                        help="Use LLM for extraction & reply enhancement")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to RFQ text file (uses built-in sample if omitted)")
    parser.add_argument("--output", type=str, default="./output",
                        help="Output directory (default: ./output)")
    args = parser.parse_args()

    mock_mode = not args.live

    if args.input:
        message_body = Path(args.input).read_text(encoding="utf-8")
        subject = Path(args.input).stem
    else:
        message_body = SAMPLE_RFQ
        subject = "RFQ - LED Lighting for Warehouse Project"
        logger.info("No --input provided. Using built-in sample RFQ.")

    result = run_pipeline(
        message_body=message_body,
        subject=subject,
        mock_mode=mock_mode,
        use_llm=args.llm,
        output_dir=args.output,
    )

    print("\n" + "="*60)
    print("PIPELINE RESULT SUMMARY")
    print("="*60)
    print(f"Status:      {result['pipeline_status']}")
    print(f"Mock mode:   {result['mock_mode']}")
    print(f"Deal ID:     {result['crm']['deal_id']}")
    print(f"Contact ID:  {result['crm']['contact_id']}")
    print(f"Items found: {len(result['rfq']['line_items'])}")
    print(f"Confidence:  {result['rfq']['confidence']*100:.0f}%")
    print(f"Attachments: {len(result['attachments'])}")
    print(f"Alert sent:  slack={result['alert']['slack_sent']} email={result['alert']['email_sent']}")
    print("\n--- English Reply Draft ---")
    print(result['reply_draft']['english'])
    print("\n--- Arabic Reply Draft ---")
    print(result['reply_draft']['arabic'])
    print("="*60)


if __name__ == "__main__":
    main()
