"""
Attachment Archiver
Saves attachments to local disk with structured naming,
optionally uploads to S3-compatible storage.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AttachmentRecord:
    original_filename: str
    stored_path: str
    size_bytes: int
    storage_backend: str  # "local" | "s3"
    s3_url: Optional[str] = None


def archive_attachments(
    attachments: List[dict],
    deal_id: str,
    storage_path: str = "./attachments",
    mock_mode: bool = True,
) -> List[AttachmentRecord]:
    """
    Archive a list of attachments.

    Args:
        attachments:  List of dicts with keys 'filename' and 'content' (bytes) or 'path'.
        deal_id:      CRM deal ID — used to organise storage by deal.
        storage_path: Root directory for local storage.
        mock_mode:    If True, creates placeholder files instead of writing real content.

    Returns:
        List of AttachmentRecord describing where each file was stored.
    """
    records: List[AttachmentRecord] = []
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    deal_dir = Path(storage_path) / deal_id / timestamp
    deal_dir.mkdir(parents=True, exist_ok=True)

    if not attachments:
        logger.info("No attachments to archive for deal %s", deal_id)
        return records

    for att in attachments:
        filename = att.get("filename", "attachment.bin")
        safe_name = _sanitize_filename(filename)
        dest_path = deal_dir / safe_name

        if mock_mode:
            # Write a placeholder
            dest_path.write_text(
                f"[MOCK ATTACHMENT PLACEHOLDER]\nOriginal: {filename}\nDeal: {deal_id}\n"
            )
            size = dest_path.stat().st_size
        elif "path" in att:
            shutil.copy2(att["path"], dest_path)
            size = dest_path.stat().st_size
        elif "content" in att:
            content = att["content"]
            if isinstance(content, str):
                content = content.encode()
            dest_path.write_bytes(content)
            size = len(content)
        else:
            logger.warning("Attachment %s has no content or path — skipping", filename)
            continue

        # Optionally upload to S3
        s3_url = None
        backend = "local"
        if not mock_mode and _s3_configured():
            s3_url = _upload_to_s3(dest_path, deal_id, safe_name)
            backend = "s3"

        records.append(
            AttachmentRecord(
                original_filename=filename,
                stored_path=str(dest_path),
                size_bytes=size,
                storage_backend=backend,
                s3_url=s3_url,
            )
        )
        logger.info(
            "Archived attachment: %s → %s (%d bytes, %s)",
            filename, dest_path, size, backend,
        )

    return records


def _sanitize_filename(name: str) -> str:
    """Remove dangerous characters from filename."""
    name = Path(name).name  # strip any directory traversal
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return safe or "attachment.bin"


def _s3_configured() -> bool:
    return bool(
        os.getenv("AWS_ACCESS_KEY_ID")
        and os.getenv("AWS_SECRET_ACCESS_KEY")
        and os.getenv("AWS_S3_BUCKET")
    )


def _upload_to_s3(local_path: Path, deal_id: str, filename: str) -> Optional[str]:
    try:
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ["AWS_S3_BUCKET"]
        key = f"rfq-attachments/{deal_id}/{filename}"
        s3.upload_file(str(local_path), bucket, key)
        region = os.getenv("AWS_REGION", "us-east-1")
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
        logger.info("Uploaded to S3: %s", url)
        return url
    except Exception as exc:
        logger.error("S3 upload failed: %s", exc)
        return None
