from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from werkzeug.datastructures import FileStorage

from backend.utils.helpers import generate_temp_path
from backend.utils.logger import get_file_logger

logger = get_file_logger("upload_service")

# Constants duplicated in upload route for shared config
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".ged", ".gedcom"}


def is_valid_gedcom_content(file: FileStorage) -> bool:
    """Basic GEDCOM sanity check: look for HEAD and TRLR records."""
    try:
        file.seek(0)
        start = file.read(1024).decode(errors="ignore")
        file.seek(-1024, os.SEEK_END)
        end = file.read(1024).decode(errors="ignore")
    except Exception:
        file.seek(0)
        return False
    finally:
        file.seek(0)
    return "0 HEAD" in start and "0 TRLR" in end


def validate_upload(file: FileStorage) -> Tuple[bool, str, float]:
    """Return (ok, message, size_mb)."""
    if not file or not file.filename:
        return False, "Missing file", 0.0

    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    size_mb = size_bytes / (1024 * 1024)
    file.seek(0)

    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File > {MAX_FILE_SIZE_MB} MB", size_mb

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Invalid file type", size_mb

    if not is_valid_gedcom_content(file):
        return False, "File content is not a valid GEDCOM file", size_mb

    return True, "", size_mb


def save_file(file: FileStorage, temp_dir: str = "/tmp") -> str:
    """Persist upload to a temporary file path and return the path."""
    tmp_name = generate_temp_path(Path(file.filename).suffix)
    path = str(Path(temp_dir) / tmp_name)
    file.seek(0)
    file.save(path)
    logger.debug("Saved uploaded file to %s", path)
    return path
