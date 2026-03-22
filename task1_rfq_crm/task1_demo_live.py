"""
Live Demo — Task 1 RFQ Pipeline with real Groq LLM
Tests real field extraction + real bilingual reply generation

Usage:
    cd task1_rfq_crm
    python demo_live.py
"""
import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")

SAMPLE_RFQ = """
From: Mohammed Al-Farsi <m.alfarsi@desert-infra.ae>
Subject: Urgent RFQ - Street and Warehouse Lighting Project

Dear Sales Team,

We are Desert Infrastructure LLC based in Abu Dhabi, UAE.
We require urgent pricing for a major government project.

Contact: Mohammed Al-Farsi, Procurement Director
Phone: +971 2 555 8890
Email: m.alfarsi@desert-infra.ae

We need the following:
250 units LED Street Light 100W for highway project
1500 units LED High Bay 150W for warehouse complex
800 units LED Panel 60W for office blocks
2000 units LED Tube 18W for corridors and parking

Destination: Abu Dhabi, UAE (Port of Khalifa)
Required delivery: Before 30th April 2025
Payment: LC at sight preferred, or 30% TT advance acceptable
Incoterms: CIF Abu Dhabi

Please quote your best prices with warranty details.
This is urgent — project deadline is tight.

Best regards,
Mohammed Al-Farsi
"""

def run_live_demo():
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your-groq" in key:
        print("ERROR: GROQ_API_KEY not set in .env file")
        sys.exit(1)
    print(f"✓ GROQ_API_KEY found (ending: ...{key[-6:]})\n")

    from rfq_processor import run_pipeline

    print("=== Running Task 1 Pipeline with Groq LLM (live mode) ===\n")
    result = run_pipeline(
        message_body=SAMPLE_RFQ,
        subject="Urgent RFQ - Street and Warehouse Lighting Project",
        mock_mode=False,
        use_llm=True,
        output_dir="./output_live",
    )

    print("\n=== RESULT SUMMARY ===")
    print(f"Status:     {result['pipeline_status']}")
    print(f"Deal ID:    {result['crm']['deal_id']}")
    print(f"Email:      {result['rfq']['sender_email']}")
    print(f"Company:    {result['rfq']['sender_company']}")
    print(f"Items:      {len(result['rfq']['line_items'])}")
    print(f"Confidence: {result['rfq']['confidence']*100:.0f}%")
    print(f"Method:     {result['rfq']['extraction_method']}")
    print(f"\n--- English Reply (Groq-generated) ---")
    print(result['reply_draft']['english'])
    print(f"\n--- Arabic Reply (Groq-generated) ---")
    print(result['reply_draft']['arabic'])

if __name__ == "__main__":
    run_live_demo()
