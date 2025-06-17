from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Tuple

from werkzeug.datastructures import FileStorage

from backend.utils.helpers import generate_temp_path
from backend.utils.logger import get_file_logger

logger = get_file_logger("upload_service")

# ────────── Public constants ──────────
MAX_FILE_SIZE_MB: int = int(os.getenv("UPLOAD_MAX_FILE_SIZE_MB", "20"))
ALLOWED_EXTENSIONS: set[str] = {".ged", ".gedcom"}

__all__ = [
    "MAX_FILE_SIZE_MB",
    "ALLOWED_EXTENSIONS",
    "validate_upload",
    "save_file",
    "cleanup_temp",
]

# ────────── Internal helpers ──────────
def _read_segment(file: FileStorage, offset: int, size: int = 1024) -> str:
    """Read a slice safely, guarding against tiny files."""
    try:
        file.seek(offset, os.SEEK_END)
    except OSError:
        file.seek(0)
    segment = file.read(size).decode(errors="ignore")
    file.seek(0)
    return segment


def is_valid_gedcom_content(file: FileStorage) -> bool:
    """Naïve GEDCOM check: at least '0 HEAD' and '0 TRLR' somewhere in the file."""
    head = file.read(1024).decode(errors="ignore")
    size = file.tell()
    tail = _read_segment(file, -min(1024, size))
    return "0 HEAD" in head and "0 TRLR" in (tail or head)


# ────────── Public API ──────────
def validate_upload(file: FileStorage) -> Tuple[bool, str, float]:
    """
    Basic validation.
    Returns (ok, message, size_mb). `message` is empty when ok=True.
    """
    if not file or not file.filename:
        return False, "Missing file. Upload a GEDCOM (.ged)", 0.0

    # Size check
    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    size_mb = size_bytes / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return (
            False,
            f"File is {size_mb:.1f} MB — maximum allowed is {MAX_FILE_SIZE_MB} MB.",
            size_mb,
        )

    # Extension check
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        return (
            False,
            f"Invalid extension: {ext}. Allowed types: {allowed}",
            size_mb,
        )

    # GEDCOM sanity check
    if not is_valid_gedcom_content(file):
        return False, "GEDCOM signature not found (missing 0 HEAD / 0 TRLR).", size_mb

    return True, "", size_mb


def save_file(file: FileStorage, temp_dir: str = "/tmp") -> str:
    """Persist upload to a temp file path and return that path."""
    tmp_name = generate_temp_path(Path(file.filename).suffix or ".ged")
    path = str(Path(temp_dir) / tmp_name)
    file.seek(0)
    file.save(path)
    logger.debug("💾 Saved upload → %s", path)
    return path


def cleanup_temp(path: str):
    """Remove temp path or directory; swallow errors but log them."""
    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
        logger.debug("🧹 Removed temp %s", path)
    except Exception as exc:
        logger.warning("⚠️ Could not remove temp %s: %s", path, exc)
