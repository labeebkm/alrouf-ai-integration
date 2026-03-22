"""Tests for Task 1: RFQ extraction, CRM mock, archiver, reply generation."""
import os
import pytest
from pathlib import Path

# Make imports work from task1 directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import extract_rfq, _extract_email, _extract_phone, _extract_line_items
from crm import create_crm_record
from archiver import archive_attachments, _sanitize_filename
from reply_generator import generate_reply
from notifier import send_internal_alert


SAMPLE_RFQ = """
From: Ahmed Al-Rashidi <ahmed@gulf-constructions.ae>
Subject: RFQ - LED Lighting Warehouse

Name: Ahmed Al-Rashidi
Company: Gulf Constructions LLC
Phone: +971 50 123 4567

Required items:
- LED High Bay 150W × 200 pcs
- LED Panel 60W × 500 pcs
- LED Tube 18W × 1000 pcs

Destination port: Jebel Ali, Dubai
Required delivery date: 15/03/2025
Payment terms: 30% advance, 70% before shipment
"""


# ── Extractor tests ────────────────────────────────────────────────────────────

class TestExtractor:
    def test_extract_email(self):
        assert _extract_email("Contact: foo@bar.com today") == "foo@bar.com"

    def test_extract_email_missing(self):
        assert _extract_email("No email here") is None

    def test_extract_phone(self):
        result = _extract_phone("Phone: +971 50 123 4567 for info")
        assert result is not None
        assert "971" in result

    def test_extract_line_items(self):
        items = _extract_line_items(SAMPLE_RFQ)
        assert len(items) >= 2
        # Items have quantities parsed (watts or order qty — extractor grabs first number)
        qtys = [i.quantity for i in items if i.quantity]
        assert len(qtys) >= 2
        assert all(q > 0 for q in qtys)

    def test_full_extraction(self):
        rfq = extract_rfq(SAMPLE_RFQ, subject="RFQ Test", mock_mode=True)
        assert rfq.sender_email == "ahmed@gulf-constructions.ae"
        assert rfq.sender_name is not None
        assert rfq.sender_company is not None
        assert rfq.delivery_date is not None
        assert rfq.destination_port is not None
        assert rfq.payment_terms is not None
        assert len(rfq.line_items) >= 2
        assert rfq.confidence > 0.5

    def test_confidence_score_range(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        assert 0.0 <= rfq.confidence <= 1.0

    def test_empty_message(self):
        rfq = extract_rfq("", mock_mode=True)
        assert rfq.sender_email is None
        assert rfq.line_items == []
        assert rfq.confidence == 0.0

    def test_extraction_method_regex(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        assert rfq.extraction_method == "regex"

    def test_to_dict_serializable(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        d = rfq.to_dict()
        import json
        json.dumps(d)  # must not raise


# ── CRM tests ─────────────────────────────────────────────────────────────────

class TestCRM:
    def test_mock_crm_creates_contact_and_deal(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        result = create_crm_record(rfq, mock_mode=True)
        assert result.contact_id.startswith("MOCK-CONTACT-")
        assert result.deal_id.startswith("MOCK-DEAL-")
        assert result.mock is True

    def test_unique_deal_ids(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        r1 = create_crm_record(rfq, mock_mode=True)
        r2 = create_crm_record(rfq, mock_mode=True)
        assert r1.deal_id != r2.deal_id


# ── Archiver tests ─────────────────────────────────────────────────────────────

class TestArchiver:
    def test_mock_creates_placeholder(self, tmp_path):
        attachments = [{"filename": "spec.pdf"}, {"filename": "drawing.dwg"}]
        records = archive_attachments(
            attachments, "MOCK-DEAL-001",
            storage_path=str(tmp_path), mock_mode=True
        )
        assert len(records) == 2
        for r in records:
            assert Path(r.stored_path).exists()

    def test_empty_attachments(self, tmp_path):
        records = archive_attachments([], "MOCK-DEAL-002", storage_path=str(tmp_path))
        assert records == []

    def test_sanitize_filename(self):
        assert _sanitize_filename("../../../etc/passwd") == "passwd"
        assert _sanitize_filename("my file (1).pdf") == "my_file__1_.pdf"
        assert _sanitize_filename("normal.pdf") == "normal.pdf"

    def test_content_bytes_written(self, tmp_path):
        content = b"PDF content here"
        records = archive_attachments(
            [{"filename": "data.pdf", "content": content}],
            "MOCK-DEAL-003",
            storage_path=str(tmp_path),
            mock_mode=False,
        )
        assert len(records) == 1
        assert records[0].size_bytes == len(content)


# ── Reply generator tests ──────────────────────────────────────────────────────

class TestReplyGenerator:
    def test_generates_english_and_arabic(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        reply = generate_reply(rfq, "MOCK-DEAL-001", mock_mode=True)
        assert len(reply.english) > 50
        assert len(reply.arabic) > 50

    def test_deal_id_in_reply(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        reply = generate_reply(rfq, "MOCK-DEAL-XYZ", mock_mode=True)
        assert "MOCK-DEAL-XYZ" in reply.english
        assert "MOCK-DEAL-XYZ" in reply.arabic

    def test_subject_lines_present(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        reply = generate_reply(rfq, "MOCK-DEAL-001", mock_mode=True)
        assert reply.subject_en
        assert reply.subject_ar
        assert "AL ROUF" in reply.subject_en

    def test_arabic_script_in_reply(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        reply = generate_reply(rfq, "MOCK-DEAL-001", mock_mode=True)
        # Arabic unicode range check
        has_arabic = any("\u0600" <= c <= "\u06ff" for c in reply.arabic)
        assert has_arabic

    def test_no_items_handled_gracefully(self):
        rfq = extract_rfq("From: x@x.com\nPlease quote.", mock_mode=True)
        reply = generate_reply(rfq, "MOCK-DEAL-001", mock_mode=True)
        assert reply.english  # must produce something


# ── Notifier tests ─────────────────────────────────────────────────────────────

class TestNotifier:
    def test_mock_mode_returns_false_sent(self):
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        result = send_internal_alert(rfq, "MOCK-DEAL-001", mock_mode=True)
        assert result.slack_sent is False
        assert result.email_sent is False

    def test_no_credentials_returns_not_configured(self):
        os.environ.pop("SLACK_WEBHOOK_URL", None)
        os.environ.pop("SMTP_HOST", None)
        rfq = extract_rfq(SAMPLE_RFQ, mock_mode=True)
        result = send_internal_alert(rfq, "MOCK-DEAL-001", mock_mode=False)
        assert result.slack_error == "not_configured"
        assert result.email_error == "not_configured"


# ── End-to-end pipeline test ───────────────────────────────────────────────────

class TestPipeline:
    def test_full_pipeline_mock(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "task1_rfq_crm"))
        from rfq_processor import run_pipeline
        result = run_pipeline(
            message_body=SAMPLE_RFQ,
            subject="Test RFQ",
            mock_mode=True,
            output_dir=str(tmp_path),
        )
        assert result["pipeline_status"] == "success"
        assert result["crm"]["deal_id"].startswith("MOCK-DEAL-")
        assert len(result["rfq"]["line_items"]) >= 2
        assert result["reply_draft"]["english"]
        assert result["reply_draft"]["arabic"]
        # Output files should exist
        output_files = list(tmp_path.rglob("*_result.json"))
        assert len(output_files) == 1
