"""Local disk storage for uploaded receipt files.

Kept separate from the services layer on purpose: the mock service only
stores a filename string against an expense, it doesn't know or care how
(or whether) the bytes are persisted. A real service implementation would
likely store receipts differently (e.g. object storage) behind its own
upload endpoint.
"""

from __future__ import annotations

import uuid
from pathlib import Path

RECEIPTS_DIR = Path(__file__).resolve().parent.parent / "media" / "receipts"


async def save_receipt(file) -> str:
    """Save an uploaded file (a nicegui FileUpload) and return its stored filename."""
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.name).suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    await file.save(RECEIPTS_DIR / stored_name)
    return stored_name


def receipt_path(filename: str) -> Path:
    return RECEIPTS_DIR / filename
