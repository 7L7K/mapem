"""Simple redaction helpers.

- Hide living persons or DOB after cutoff year unless authorized
"""
from __future__ import annotations

from datetime import date
from typing import Optional


DEFAULT_CUTOFF_YEAR = 1950


def is_authorized(headers: dict | None) -> bool:
    """Very lightweight auth check via header.

    If the request carries X-Viewer-Role: admin, allow full details.
    """
    if not headers:
        return False
    role = (headers.get("X-Viewer-Role") or headers.get("x-viewer-role") or "").lower()
    return role == "admin"


def should_redact_person(
    birth_date: Optional[date],
    death_date: Optional[date],
    *,
    cutoff_year: int = DEFAULT_CUTOFF_YEAR,
) -> bool:
    """Return True if a person's details should be redacted.

    Rules:
    - If death_date is present and <= cutoff_year → not redacted
    - Else if birth_date is present and year > cutoff_year → redacted
    - Else if death_date missing and birth_date missing or not trustworthy → redacted (assume living)
    """
    # If we know they died on/before cutoff, show
    if death_date and death_date.year <= cutoff_year:
        return False

    # If born after cutoff, hide
    if birth_date and birth_date.year > cutoff_year:
        return True

    # If no death record, default to redacted (erring on privacy)
    if not death_date:
        return True

    return False


def redact_name(name: str | None) -> str:
    return "Private" if name else "Private"


