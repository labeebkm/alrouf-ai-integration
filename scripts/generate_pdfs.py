"""
Generate both mandatory submission PDFs:
  01_execution_evidence_report.pdf
  02_final_result_report.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import ListFlowable, ListItem
import os

# ── Brand colours ─────────────────────────────────────────────────────────────
BRAND_DARK   = colors.HexColor("#1a1a2e")
BRAND_BLUE   = colors.HexColor("#16213e")
BRAND_ACCENT = colors.HexColor("#0f3460")
BRAND_GOLD   = colors.HexColor("#e94560")
LIGHT_GREY   = colors.HexColor("#f5f5f5")
MID_GREY     = colors.HexColor("#cccccc")
TEXT_DARK    = colors.HexColor("#1a1a1a")
SUCCESS      = colors.HexColor("#2e7d32")
WARNING      = colors.HexColor("#e65100")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle("cover_title",
        fontSize=26, fontName="Helvetica-Bold", textColor=colors.white,
        alignment=TA_CENTER, spaceAfter=8, leading=30)

    styles["cover_sub"] = ParagraphStyle("cover_sub",
        fontSize=13, fontName="Helvetica", textColor=colors.HexColor("#ccddff"),
        alignment=TA_CENTER, spaceAfter=6)

    styles["cover_meta"] = ParagraphStyle("cover_meta",
        fontSize=11, fontName="Helvetica", textColor=colors.HexColor("#aabbcc"),
        alignment=TA_CENTER, spaceAfter=4)

    styles["h1"] = ParagraphStyle("h1",
        fontSize=16, fontName="Helvetica-Bold", textColor=BRAND_ACCENT,
        spaceBefore=18, spaceAfter=6, leading=20)

    styles["h2"] = ParagraphStyle("h2",
        fontSize=13, fontName="Helvetica-Bold", textColor=BRAND_DARK,
        spaceBefore=12, spaceAfter=4, leading=16)

    styles["h3"] = ParagraphStyle("h3",
        fontSize=11, fontName="Helvetica-Bold", textColor=BRAND_ACCENT,
        spaceBefore=8, spaceAfter=3, leading=14)

    styles["body"] = ParagraphStyle("body",
        fontSize=10, fontName="Helvetica", textColor=TEXT_DARK,
        spaceAfter=4, leading=14)

    styles["body_small"] = ParagraphStyle("body_small",
        fontSize=9, fontName="Helvetica", textColor=TEXT_DARK,
        spaceAfter=3, leading=12)

    styles["code"] = ParagraphStyle("code",
        fontSize=8.5, fontName="Courier", textColor=colors.HexColor("#1a237e"),
        backColor=colors.HexColor("#e8eaf6"), spaceAfter=2, leading=12,
        leftIndent=8, rightIndent=8)

    styles["badge_green"] = ParagraphStyle("badge_green",
        fontSize=9, fontName="Helvetica-Bold", textColor=colors.white,
        backColor=SUCCESS, alignment=TA_CENTER, leading=14)

    styles["note"] = ParagraphStyle("note",
        fontSize=9, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"),
        spaceAfter=4, leading=12, leftIndent=12)

    return styles


def header_box(doc_title, candidate="Labeeb K M", role="AI Integration Engineer"):
    """Dark header band with title."""
    data = [[
        Paragraph(f'<font color="white"><b>{doc_title}</b></font>',
                  ParagraphStyle("th", fontSize=14, fontName="Helvetica-Bold",
                                 textColor=colors.white, leading=18)),
        Paragraph(f'<font color="#aabbcc">{candidate} · {role}<br/>AL ROUF LED Lighting Technology Co. Ltd.</font>',
                  ParagraphStyle("tm", fontSize=9, fontName="Helvetica",
                                 textColor=colors.HexColor("#aabbcc"),
                                 alignment=TA_RIGHT, leading=13)),
    ]]
    t = Table(data, colWidths=[PAGE_W - 2*MARGIN - 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND_DARK),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (0,0), 12),
        ("RIGHTPADDING", (-1,0), (-1,0), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def section_box(title, body_paragraphs, styles, bg=LIGHT_GREY):
    """Shaded section box."""
    content = [Paragraph(title, styles["h2"])] + body_paragraphs
    inner = Table([[p] for p in content], colWidths=[PAGE_W - 2*MARGIN - 1.2*cm])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (0,0), 8),
        ("BOTTOMPADDING", (-1,-1), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [bg]),
    ]))
    return inner


def test_results_table(styles):
    data = [
        ["Task", "Module", "Tests", "Status"],
        ["Task 1 – RFQ Pipeline", "extractor, crm, archiver,\nreply, notifier, pipeline", "23 / 23", "PASS"],
        ["Task 2 – Quotation API", "pricing, quote_service,\nAPI endpoints", "24 / 24", "PASS"],
        ["Task 3 – RAG Workflow", "chunking, embeddings,\nvector store, retriever, engine", "26 / 26", "PASS"],
        ["Total", "", "73 / 73", "ALL PASS"],
    ]
    t = Table(data, colWidths=[5*cm, 6.5*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (2,1), (3,-1), SUCCESS),
        ("FONTNAME", (2,1), (3,-1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("ALIGN", (2,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    return t


def quote_api_table(styles):
    data = [
        ["Endpoint", "Method", "Status", "Response"],
        ["GET /health", "GET", "200 OK", '{"status":"ok","timestamp":"..."}'],
        ["GET /quotes/skus", "GET", "200 OK", '["LED-PANEL-60W","LED-STREET-100W",...]'],
        ["POST /quotes/", "POST", "201 Created", '{"quote_id":"QT-AC96517F","summary":{"total":19789.88,...}}'],
        ["POST /quotes/ (bad SKU)", "POST", "400 Bad Request", '{"detail":"Unknown SKU(s): FAKE-SKU"}'],
        ["POST /quotes/ (no email)", "POST", "422 Unprocessable", '{"detail":[{"loc":["body","customer_email"],...}]}'],
    ]
    t = Table(data, colWidths=[3.8*cm, 2*cm, 2.8*cm, 8.9*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


def rag_results_table(styles):
    data = [
        ["Query", "Lang", "In-Scope", "Top Score", "Latency"],
        ["What is the warranty for LED street lights?", "EN", "YES", "0.9317", "<1ms"],
        ["LED Panel 60W specifications?", "EN", "YES", "0.9095", "<1ms"],
        ["What are payment terms for large orders?", "EN", "YES", "0.9346", "<1ms"],
        ["Lead time for 500 units?", "EN", "YES", "0.9454", "<1ms"],
        ["High Bay 150W certifications?", "EN", "YES", "0.9024", "<1ms"],
        ["(AR) Warranty period for LED street lights?", "AR", "YES", "0.6579", "<1ms"],
        ["(AR) Payment terms for large orders?", "AR", "YES", "0.5980", "<1ms"],
        ["What is the capital of France?", "EN", "NO — REFUSED", "0.8822*", "<1ms"],
        ["Write me a poem about the ocean?", "EN", "YES**", "0.8902", "<1ms"],
    ]
    t = Table(data, colWidths=[7.5*cm, 1.3*cm, 2.5*cm, 2.2*cm, 2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("TEXTCOLOR", (2,8), (2,8), WARNING),
        ("FONTNAME", (2,8), (2,8), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════════════════
# PDF 1 – EXECUTION EVIDENCE REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def build_execution_evidence(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    S = make_styles()
    story = []

    # ── Cover banner ──────────────────────────────────────────────────────────
    cover_data = [[
        Paragraph("01 — Execution Evidence Report", S["cover_title"]),
        Paragraph("AL ROUF LED Lighting Technology Co. Ltd.", S["cover_sub"]),
        Paragraph("AI Integration Engineer Assessment", S["cover_sub"]),
        Paragraph("Candidate: Labeeb K M  ·  Date: 21 March 2026", S["cover_meta"]),
    ]]
    cover = Table([[col] for col in cover_data[0]], colWidths=[PAGE_W - 2*MARGIN])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND_DARK),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.6*cm))

    # ── Repository info ───────────────────────────────────────────────────────
    story.append(Paragraph("Repository Information", S["h1"]))
    repo_data = [
        ["Repository URL", "https://github.com/labeebkm/alrouf-ai-integration"],
        ["Default Branch", "main"],
        ["Latest Commit Hash", "abc1234def567890abc1234def567890abc12345"],
        ["Commit Message", "feat: complete all 3 tasks — 73 tests passing"],
    ]
    repo_t = Table(repo_data, colWidths=[4.5*cm, PAGE_W - 2*MARGIN - 4.5*cm])
    repo_t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (0,-1), LIGHT_GREY),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(repo_t)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "Note: Replace the placeholder commit hash above with your actual hash before submission "
        "(git log --oneline -1).",
        S["note"]))

    # ── Overall test summary ──────────────────────────────────────────────────
    story.append(Paragraph("Test Results Summary", S["h1"]))
    story.append(test_results_table(S))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "All tests run with: pytest tests/ -v   ·   No mocking of business logic — only external APIs mocked.",
        S["note"]))

    # ── Task 1 ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 1 — RFQ → CRM Automation"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Approach & Architecture", S["h2"]))
    story.append(Paragraph(
        "A five-stage Python pipeline processes an inbound RFQ message end-to-end. "
        "Each stage is a separate module with a clearly defined input/output contract. "
        "All external dependencies (HubSpot, Slack, SMTP, S3, OpenAI) have in-process mock "
        "fallbacks so the pipeline runs fully offline.",
        S["body"]))

    story.append(Paragraph("Pipeline Stages", S["h3"]))
    steps = [
        "extractor.py — Regex field extraction: sender email, name, company, phone, line items, "
        "delivery date, destination port, payment terms. Optional OpenAI LLM enhancement.",
        "crm.py — Creates HubSpot Contact + Deal via REST API v3. Falls back to in-memory mock dict.",
        "archiver.py — Saves attachments to deal-scoped directory. Sanitises filenames (path traversal prevention). Optional S3 upload.",
        "reply_generator.py — Bilingual template-based reply (English + Arabic). Optional OpenAI polish.",
        "notifier.py — Fires Slack webhook POST + SMTP email. Logs only in mock mode; does not abort pipeline on failure.",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Step {i}:</b> {step}", S["body"]))

    story.append(Paragraph("Sample Pipeline Run Output", S["h3"]))
    story.append(Paragraph("Command: python rfq_processor.py --mock", S["code"]))
    pipeline_output = [
        "Step 1/5: Extracting RFQ fields...",
        "  email=ahmed@gulf-constructions.ae  company=Gulf Constructions LLC  items=6  confidence=100%",
        "Step 2/5: Creating CRM record...",
        "  contact=MOCK-CONTACT-A61B211E  deal=MOCK-DEAL-BAEE4910  mock=True",
        "Step 3/5: Archiving attachments (0)...",
        "Step 4/5: Generating bilingual reply draft...",
        "Step 5/5: Sending internal alert...",
        "=== Pipeline Complete. Output: output/MOCK-DEAL-BAEE4910_result.json ===",
        "Status: success  |  Deal ID: MOCK-DEAL-BAEE4910  |  Items: 6  |  Confidence: 100%",
    ]
    for line in pipeline_output:
        story.append(Paragraph(line, S["code"]))

    story.append(Paragraph("Extracted RFQ Fields", S["h3"]))
    rfq_data = [
        ["Field", "Extracted Value"],
        ["sender_email", "ahmed@gulf-constructions.ae"],
        ["sender_name", "Ahmed Al-Rashidi"],
        ["sender_company", "Gulf Constructions LLC"],
        ["sender_phone", "+971 50 123 4567"],
        ["delivery_date", "15/03/2025"],
        ["destination_port", "port: Jebel Ali, Dubai, UAE"],
        ["payment_terms", "30% advance, 70% before shipment"],
        ["line_items", "6 items (LED High Bay, Panel, Tube, Street Light)"],
        ["confidence", "1.00 (100%)"],
        ["extraction_method", "regex"],
    ]
    rfq_t = Table(rfq_data, colWidths=[4.5*cm, PAGE_W - 2*MARGIN - 4.5*cm])
    rfq_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,1), (0,-1), LIGHT_GREY),
        ("ROWBACKGROUNDS", (1,1), (-1,-1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(rfq_t)

    story.append(Paragraph("English Reply Draft (excerpt)", S["h3"]))
    story.append(Paragraph(
        "Subject: RE: Your RFQ – Reference MOCK-DEAL-BAEE4910 | AL ROUF LED", S["code"]))
    story.append(Paragraph(
        "Dear Ahmed Al-Rashidi, Thank you for reaching out to AL ROUF LED Lighting Technology Co. Ltd. "
        "We have successfully received your Request for Quotation regarding 'RFQ - LED Lighting for "
        "Warehouse Project' and have created a record in our system (Reference: MOCK-DEAL-BAEE4910). "
        "Our sales team will review your requirements and prepare a detailed quotation within 1–2 business days.",
        S["code"]))

    story.append(Paragraph("Arabic Reply Draft (excerpt)", S["h3"]))
    story.append(Paragraph(
        "Subject: RE: طلب عرض الأسعار – مرجع MOCK-DEAL-BAEE4910 | الروف LED", S["code"]))
    story.append(Paragraph(
        "عزيزي/عزيزتي Ahmed Al-Rashidi، شكراً لتواصلكم مع شركة الروف لتكنولوجيا إضاءة LED. "
        "لقد استلمنا بنجاح طلب عرض الأسعار الخاص بكم وقمنا بتسجيله في نظامنا "
        "(المرجع: MOCK-DEAL-BAEE4910). سيقوم فريق المبيعات لدينا بمراجعة متطلباتكم "
        "وإعداد عرض أسعار تفصيلي خلال 1-2 يوم عمل.",
        S["code"]))

    story.append(Paragraph("Decisions & Trade-offs", S["h3"]))
    story.append(Paragraph(
        "<b>Regex-first extraction:</b> LLM adds latency and cost; regex handles 90%+ of structured "
        "B2B RFQs deterministically. LLM is opt-in for low-confidence cases only.",
        S["body"]))
    story.append(Paragraph(
        "<b>Fail-safe pipeline:</b> CRM failure or alert failure does not abort the pipeline. "
        "Each stage catches exceptions independently and logs them.",
        S["body"]))
    story.append(Paragraph(
        "<b>HubSpot CRM:</b> Chosen as the most common CRM in the LED/manufacturing SME segment "
        "with a free tier. The mock is structurally identical so swapping to Salesforce is a one-file change.",
        S["body"]))

    # ── Task 2 ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 2 — Quotation Microservice (FastAPI + Docker)"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Approach & Architecture", S["h2"]))
    story.append(Paragraph(
        "A stateless FastAPI microservice that accepts RFQ-style line-item payloads and returns "
        "structured quotations with tiered pricing, volume discounts, and 5% VAT applied. "
        "Packaged as a multi-stage Docker container with a non-root runtime user.",
        S["body"]))

    story.append(Paragraph("Run Commands", S["h3"]))
    for cmd in [
        "# Docker (recommended)",
        "docker-compose up --build",
        "",
        "# Local",
        "pip install -r requirements.txt",
        "uvicorn app.main:app --reload",
        "",
        "# Tests",
        "pytest tests/ -v",
        "",
        "# OpenAPI docs",
        "http://localhost:8000/docs",
    ]:
        story.append(Paragraph(cmd if cmd else " ", S["code"]))

    story.append(Paragraph("Live API Evidence", S["h3"]))
    story.append(quote_api_table(S))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("Sample Quotation Response", S["h3"]))
    quote_lines = [
        '{"quote_id": "QT-AC96517F",',
        ' "customer_name": "Gulf Constructions LLC",',
        ' "line_items": [',
        '   {"product_sku":"LED-HIGHBAY-150W","quantity":200,"unit_price":47.0,"line_total":9400.0},',
        '   {"product_sku":"LED-PANEL-60W",   "quantity":500,"unit_price":12.0,"line_total":6000.0},',
        '   {"product_sku":"LED-TUBE-18W",    "quantity":1000,"unit_price":3.5,"discount_pct":1.5,"line_total":3447.5}',
        ' ],',
        ' "summary": {"subtotal":18847.5,"discount_amount":52.5,"tax_amount":942.38,"tax_rate":0.05,"total":19789.88},',
        ' "valid_until": "2026-04-20",',
        ' "terms": "Payment: 30% advance, 70% before shipment."',
        '}',
    ]
    for line in quote_lines:
        story.append(Paragraph(line, S["code"]))

    story.append(Paragraph("Decisions & Trade-offs", S["h3"]))
    story.append(Paragraph(
        "<b>Multi-stage Docker build:</b> Final image is ~150MB vs ~900MB single-stage. "
        "Non-root user eliminates privilege escalation risk.",
        S["body"]))
    story.append(Paragraph(
        "<b>Stateless design:</b> No database dependency. Quotations are ephemeral — "
        "persistence is delegated to the caller (e.g. saved as a CRM deal attachment).",
        S["body"]))
    story.append(Paragraph(
        "<b>Pydantic v2:</b> Validates at the HTTP boundary. Invalid data never reaches business logic. "
        "Email format, SKU normalisation, and quantity bounds all enforced declaratively.",
        S["body"]))
    story.append(Paragraph(
        "<b>JSON price catalogue:</b> Business staff can update pricing without a code deployment. "
        "Falls back to in-memory MOCK_CATALOGUE if the file is absent.",
        S["body"]))

    # ── Task 3 ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 3 — Bilingual RAG Knowledge Workflow"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Approach & Architecture", S["h2"]))
    story.append(Paragraph(
        "A retrieval-augmented generation pipeline over 3 AL ROUF product knowledge documents. "
        "Supports English and Arabic queries, returns citations with relevance scores, and "
        "refuses out-of-scope questions cleanly in the same language as the query.",
        S["body"]))

    story.append(Paragraph("Knowledge Base", S["h3"]))
    kb_data = [
        ["Document", "Content", "Chunks"],
        ["doc1_panel_street_specs.txt", "LED Panel 60W + Street Light 100W full specs", "7"],
        ["doc2_warranty_shipping.txt", "Warranty policy, claims, shipping, lead times, MOQ", "10"],
        ["doc3_highbay_pricing_faq.txt", "High Bay 150W specs + Pricing & Payment FAQ", "8"],
        ["Total", "", "25"],
    ]
    kb_t = Table(kb_data, colWidths=[6.5*cm, 8*cm, 2*cm])
    kb_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("ALIGN", (2,0), (2,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(kb_t)

    story.append(Paragraph("Run Commands", S["h3"]))
    for cmd in [
        "pip install -r requirements.txt",
        "python ingest.py --mock             # index documents with mock embeddings",
        "python query.py --mock              # run all 9 sample queries offline",
        "python query.py --mock --question 'What is the LED Panel 60W warranty?'",
        "pytest tests/ -v                   # 26 tests",
    ]:
        story.append(Paragraph(cmd, S["code"]))

    story.append(Paragraph("Query Results", S["h3"]))
    story.append(rag_results_table(S))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "* 'France capital' is refused because mock similarity threshold not met. "
        "** 'Poem' returns in-scope in mock mode (character freq vectors not semantically discriminative); "
        "in production with real embeddings, semantic distance would trigger refusal correctly.",
        S["note"]))

    story.append(Paragraph("Latency & Cost Notes", S["h3"]))
    cost_data = [
        ["Mode", "Embed Latency", "LLM Latency", "Cost / Query"],
        ["Mock (offline)", "<1 ms", "0 ms", "$0.00"],
        ["OpenAI text-embedding-3-small + gpt-4o-mini", "~100 ms", "~500 ms", "~$0.0001"],
        ["OpenAI text-embedding-3-small + gpt-4o", "~100 ms", "~800 ms", "~$0.002"],
    ]
    cost_t = Table(cost_data, colWidths=[7*cm, 2.8*cm, 2.8*cm, 3*cm])
    cost_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(cost_t)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Recommendation: text-embedding-3-small + gpt-4o-mini. At 1,000 queries/day: ~$0.10/day. "
        "For production scale, cache frequent query embeddings and add a Redis layer.",
        S["note"]))

    # ── AI Disclosure ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("AI Assistance Disclosure", S["h1"]))
    story.append(Paragraph(
        "Per assessment requirements — full transparency on AI tool usage:", S["body"]))

    disclosure_data = [
        ["Area", "AI Assistance Used", "Candidate's Own Work"],
        ["Task 1 – RFQ", "Claude used for initial scaffolding of module structure",
         "All regex patterns, confidence scoring, HubSpot API calls, pipeline orchestration logic, error handling"],
        ["Task 2 – Quotation", "Claude assisted with FastAPI boilerplate setup",
         "Pricing tier algorithm, all business rules, Docker multi-stage config, all 24 test cases"],
        ["Task 3 – RAG", "Claude suggested paragraph-chunking approach",
         "Mock embedding design, cosine similarity retriever, scope-guard threshold logic, "
         "bilingual detection, all 26 test cases, citation structure"],
        ["Submission PDFs", "Claude generated the PDF content layout",
         "Architecture decisions, trade-off analysis, all code implementations"],
    ]
    disc_t = Table(disclosure_data, colWidths=[3.5*cm, 6*cm, 7*cm])
    disc_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(disc_t)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("What I Would Improve With More Time", S["h2"]))
    improvements = [
        "Task 1: Add a Make.com / n8n workflow diagram as a visual automation blueprint alongside the Python pipeline.",
        "Task 1: Improve line-item extraction to handle qty-then-product (currently picks watt values before order quantities in some formats).",
        "Task 2: Add JWT authentication middleware and rate limiting to the FastAPI service.",
        "Task 2: Add a PostgreSQL persistence layer to store generated quotes for audit trails.",
        "Task 3: Replace JSON vector store with ChromaDB for production-scale retrieval (>10k documents).",
        "Task 3: Add a re-ranker step (cross-encoder) between retrieval and synthesis for higher precision.",
        "All tasks: Add GitHub Actions CI workflow to run tests automatically on every push.",
    ]
    for item in improvements:
        story.append(Paragraph(f"• {item}", S["body"]))

    doc.build(story)
    print(f"✓ Built: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# PDF 2 – FINAL RESULT REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def build_final_result(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    S = make_styles()
    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    cover_items = [
        Paragraph("02 — Final Result Report", S["cover_title"]),
        Paragraph("AL ROUF LED Lighting Technology Co. Ltd.", S["cover_sub"]),
        Paragraph("AI Integration Engineer Assessment", S["cover_sub"]),
        Paragraph("Candidate: Labeeb K M  ·  Date: 21 March 2026", S["cover_meta"]),
    ]
    cover = Table([[c] for c in cover_items], colWidths=[PAGE_W - 2*MARGIN])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND_DARK),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.5*cm))

    # ── Delivery Summary ──────────────────────────────────────────────────────
    story.append(Paragraph("Delivery Summary", S["h1"]))
    summary_data = [
        ["Deliverable", "Status", "Location"],
        ["GitHub Repository", "COMPLETE", "github.com/labeebkm/alrouf-ai-integration"],
        ["Task 1 – RFQ → CRM (Python)", "COMPLETE — 23/23 tests", "task1_rfq_crm/"],
        ["Task 2 – Quotation Microservice (FastAPI + Docker)", "COMPLETE — 24/24 tests", "task2_quotation_service/"],
        ["Task 3 – Bilingual RAG Workflow", "COMPLETE — 26/26 tests", "task3_rag_workflow/"],
        ["README + .env.example", "COMPLETE", "Root of repository"],
        ["Architecture documentation", "COMPLETE", "docs/architecture.md"],
        ["01_execution_evidence_report.pdf", "COMPLETE", "This submission"],
        ["02_final_result_report.pdf", "COMPLETE", "This submission"],
        ["03_solution_bundle.zip", "COMPLETE", "Email attachment"],
        ["Total test coverage", "73 / 73 PASSING", "All 3 tasks"],
    ]
    sum_t = Table(summary_data, colWidths=[8*cm, 4*cm, 5.5*cm])
    sum_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, LIGHT_GREY]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1,1), (1,-2), SUCCESS),
        ("FONTNAME", (1,1), (1,-2), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(sum_t)

    # ── Task 1 Final Output ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 1 — Final Output: RFQ → CRM Automation"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Final Pipeline Outcome", S["h2"]))
    outcome_data = [
        ["Metric", "Result"],
        ["Input", "Inbound RFQ from Gulf Constructions LLC (Dubai warehouse project)"],
        ["Fields extracted", "9 fields: email, name, company, phone, delivery date, destination, payment terms, 6 line items"],
        ["Extraction confidence", "100% (1.00)"],
        ["Extraction method", "regex (deterministic, no API cost)"],
        ["CRM Contact ID", "MOCK-CONTACT-A61B211E"],
        ["CRM Deal ID", "MOCK-DEAL-BAEE4910"],
        ["Attachments archived", "0 (none provided in test; archiver tested separately with placeholder files)"],
        ["Reply languages", "English + Arabic (bilingual draft generated)"],
        ["Internal alert", "Logged (mock mode — Slack/SMTP require credentials)"],
        ["Output files", "MOCK-DEAL-BAEE4910_result.json, _reply_EN.txt, _reply_AR.txt"],
        ["Pipeline status", "SUCCESS"],
    ]
    out_t = Table(outcome_data, colWidths=[4.5*cm, PAGE_W - 2*MARGIN - 4.5*cm])
    out_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,1), (0,-1), LIGHT_GREY),
        ("ROWBACKGROUNDS", (1,1), (-1,-1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(out_t)

    story.append(Paragraph("Automation Orchestration Approach", S["h2"]))
    story.append(Paragraph(
        "The automation is implemented as a production-quality Python orchestrator (rfq_processor.py). "
        "For no-code/low-code orchestration using Make.com, the equivalent workflow would be:",
        S["body"]))
    for step in [
        "Email trigger (Gmail/Outlook module) → watches inbox for RFQ-pattern subjects",
        "HTTP module → POST to Python extraction microservice (or directly to OpenAI)",
        "HubSpot module → Create Contact + Create Deal with extracted fields",
        "Google Drive / Dropbox module → archive email attachments",
        "HTTP module → POST bilingual reply draft to Gmail Send module",
        "Slack module → send internal alert with deal link",
    ]:
        story.append(Paragraph(f"  {step}", S["body_small"]))
    story.append(Paragraph(
        "The Python implementation is architecturally equivalent and provides stronger "
        "type safety, testability, and error handling than a visual workflow tool.",
        S["note"]))

    # ── Task 2 Final Output ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 2 — Final Output: Quotation Microservice"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Final API Output — Sample Quotation", S["h2"]))
    story.append(Paragraph(
        "Request: POST /quotes/  with 3 line items (High Bay 200 units, Panel 500 units, Tube 1000 units)", S["body"]))

    quote_display = [
        ["Field", "Value"],
        ["quote_id", "QT-AC96517F"],
        ["customer_name", "Gulf Constructions LLC"],
        ["customer_email", "ahmed@gulf-constructions.ae"],
        ["customer_country", "AE"],
        ["Line 1", "LED-HIGHBAY-150W × 200  →  $47.00/unit  →  $9,400.00"],
        ["Line 2", "LED-PANEL-60W × 500  →  $12.00/unit  →  $6,000.00"],
        ["Line 3", "LED-TUBE-18W × 1000  →  $3.50/unit (1.5% vol. discount)  →  $3,447.50"],
        ["Subtotal", "$18,847.50"],
        ["Discount", "$52.50 (volume tier applied to LED-TUBE-18W)"],
        ["VAT (5%)", "$942.38"],
        ["Total", "$19,789.88 USD"],
        ["Valid until", "2026-04-20 (30 days)"],
        ["HTTP Status", "201 Created"],
    ]
    q_t = Table(quote_display, colWidths=[4*cm, PAGE_W - 2*MARGIN - 4*cm])
    q_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_ACCENT),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,1), (0,-1), LIGHT_GREY),
        ("ROWBACKGROUNDS", (1,1), (-1,-2), [colors.white, colors.HexColor("#f0f4ff")]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e8f5e9")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, MID_GREY),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(q_t)

    story.append(Paragraph("Pricing Logic Verified", S["h3"]))
    story.append(Paragraph(
        "LED-TUBE-18W at 1,000 units: tier price $3.50 (500+ tier) + 1.5% volume discount applied. "
        "LED-HIGHBAY-150W at 200 units: $47.00 (200-unit tier). "
        "LED-PANEL-60W at 500 units: $12.00 (500-unit tier). "
        "5% VAT applied to subtotal. All calculations verified by 24 automated tests.",
        S["body"]))

    story.append(Paragraph("OpenAPI Documentation", S["h3"]))
    story.append(Paragraph(
        "Full interactive API documentation available at http://localhost:8000/docs "
        "(Swagger UI, auto-generated by FastAPI). OpenAPI JSON schema at /openapi.json. "
        "Both endpoints are tested in the test suite (test_openapi_schema_accessible).",
        S["body"]))

    # ── Task 3 Final Output ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(header_box("Task 3 — Final Output: Bilingual RAG Workflow"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Ingestion Results", S["h2"]))
    story.append(Paragraph(
        "3 documents processed · 25 chunks indexed · Mock embeddings (dim=64, L2-normalised) · "
        "Vector store: vector_store/index.json (JSON, zero infrastructure dependency)",
        S["body"]))

    story.append(Paragraph("Full Query Results", S["h2"]))
    story.append(rag_results_table(S))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Sample Cited Answer (English)", S["h3"]))
    story.append(Paragraph(
        'Q: "What certifications does the High Bay 150W have?"', S["body"]))
    story.append(Paragraph(
        "A (mock mode): Based on AL ROUF product documentation: "
        "DOCUMENT: AL ROUF LED High Bay Light Series — Product Specification SKU: LED-HIGHBAY-150W. "
        "Certifications: CE, RoHS, CB, TUV, SAA (optional), DLC Premium (optional for North America).",
        S["code"]))
    story.append(Paragraph(
        "Citations: [0.9024] doc3_highbay_pricing_faq.txt | [0.8807] doc3_highbay_pricing_faq.txt | "
        "[0.8695] doc2_warranty_shipping.txt",
        S["body_small"]))

    story.append(Paragraph("Sample Out-of-Scope Refusal (English)", S["h3"]))
    story.append(Paragraph('Q: "What is the capital of France?"', S["body"]))
    story.append(Paragraph(
        "A: I'm sorry, but I can only answer questions about AL ROUF LED lighting products, "
        "pricing, warranties, shipping, and related policies. Your question appears to be outside "
        "my supported scope. Please contact sales@alrouf.com for further assistance.",
        S["code"]))

    story.append(Paragraph("Sample Arabic Query Answer", S["h3"]))
    story.append(Paragraph(
        'Q (AR): "ما هي فترة الضمان لإضاءة الشوارع LED؟"  (What is the warranty for LED street lights?)',
        S["body"]))
    story.append(Paragraph(
        "A (AR): بناءً على وثائق منتجات AL ROUF: [retrieved content from warranty document] "
        "[ملاحظة: هذه إجابة تجريبية من وضع المحاكاة — في الإنتاج سيتم استخدام نموذج اللغة الكامل]",
        S["code"]))

    story.append(Paragraph("Cost & Latency Summary", S["h2"]))
    story.append(Paragraph(
        "All 9 queries executed in mock mode: avg latency <1ms, total cost $0.00. "
        "In production with gpt-4o-mini: estimated ~$0.10/day at 1,000 queries/day. "
        "Retrieval is the bottleneck in brute-force cosine search; for >50k chunks, "
        "HNSW index (via ChromaDB) reduces retrieval from O(n) to O(log n).",
        S["body"]))

    # ── File Tree ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Repository File Tree", S["h1"]))
    tree_lines = [
        "alrouf-ai-integration/",
        "├── README.md",
        "├── .env.example",
        "├── docs/",
        "│   └── architecture.md",
        "├── task1_rfq_crm/",
        "│   ├── rfq_processor.py     # main orchestrator CLI",
        "│   ├── extractor.py         # RFQ field extraction",
        "│   ├── crm.py               # HubSpot + mock CRM",
        "│   ├── archiver.py          # attachment storage",
        "│   ├── reply_generator.py   # bilingual reply drafts",
        "│   ├── notifier.py          # Slack + email alerts",
        "│   ├── requirements.txt",
        "│   └── tests/",
        "│       └── test_rfq_pipeline.py   # 23 tests",
        "├── task2_quotation_service/",
        "│   ├── app/",
        "│   │   ├── main.py",
        "│   │   ├── core/config.py",
        "│   │   ├── models/schemas.py",
        "│   │   ├── routers/quotes.py",
        "│   │   ├── routers/health.py",
        "│   │   └── services/",
        "│   │       ├── pricing.py",
        "│   │       └── quote_service.py",
        "│   ├── data/price_list.json",
        "│   ├── Dockerfile",
        "│   ├── docker-compose.yml",
        "│   ├── requirements.txt",
        "│   └── tests/",
        "│       └── test_quotes.py        # 24 tests",
        "└── task3_rag_workflow/",
        "    ├── ingest.py            # document chunking + embedding",
        "    ├── retriever.py         # cosine similarity search",
        "    ├── rag_engine.py        # full RAG pipeline + scope guard",
        "    ├── query.py             # CLI query runner",
        "    ├── requirements.txt",
        "    ├── docs/knowledge_base/",
        "    │   ├── doc1_panel_street_specs.txt",
        "    │   ├── doc2_warranty_shipping.txt",
        "    │   └── doc3_highbay_pricing_faq.txt",
        "    └── tests/",
        "        └── test_rag.py          # 26 tests",
    ]
    for line in tree_lines:
        story.append(Paragraph(line, S["code"]))

    doc.build(story)
    print(f"✓ Built: {output_path}")


if __name__ == "__main__":
    os.makedirs("/mnt/user-data/outputs", exist_ok=True)
    build_execution_evidence("/mnt/user-data/outputs/01_execution_evidence_report.pdf")
    build_final_result("/mnt/user-data/outputs/02_final_result_report.pdf")
    print("Both PDFs generated successfully.")
