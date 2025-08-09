"""
Pragmatic ML assist hooks:
 - OCR: extract likely dates/places from text using regex heuristics (placeholder for Tesseract/Cloud Vision).
 - NER: use spaCy (if available) to extract GPE and DATE from free-form notes.
Both return low-confidence suggestions; do not modify ground truth.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger("mapem.ml_assists")

try:  # optional spaCy
    import spacy  # type: ignore
    _NLP = spacy.load("en_core_web_sm")  # may fail if model not installed
except Exception:  # pragma: no cover
    _NLP = None


def ocr_extract_hints(text: str) -> List[Dict[str, str]]:
    """
    Extremely simple regex-based extractor for place/date-like strings.
    Intended as a placeholder when OCR text is provided.
    Returns list of {type: "DATE"|"PLACE", "value": str, "confidence": "low"}.
    """
    hints: List[Dict[str, str]] = []
    if not text:
        return hints

    # DATE patterns: YYYY, DD MMM YYYY, MMM YYYY
    for m in re.finditer(r"\b(\d{4})\b", text):
        yr = m.group(1)
        if 1500 <= int(yr) <= 2100:
            hints.append({"type": "DATE", "value": yr, "confidence": "low"})

    for m in re.finditer(r"\b(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b", text, re.IGNORECASE):
        hints.append({"type": "DATE", "value": m.group(1), "confidence": "low"})

    # PLACE heuristics: comma-separated capitalized tokens
    for m in re.finditer(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*,\s*[A-Z][a-zA-Z]+)\b", text):
        hints.append({"type": "PLACE", "value": m.group(1), "confidence": "low"})

    return hints


def ner_extract(text: str) -> List[Dict[str, str]]:
    """
    Use spaCy (if available) to extract GPE and DATE entities.
    Returns list of {type, value, confidence}.
    """
    out: List[Dict[str, str]] = []
    if not text:
        return out
    if not _NLP:
        logger.info("spaCy not available; NER disabled")
        return out
    try:
        doc = _NLP(text)
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC"):
                out.append({"type": "PLACE", "value": ent.text, "confidence": "very_low"})
            elif ent.label_ == "DATE":
                out.append({"type": "DATE", "value": ent.text, "confidence": "very_low"})
    except Exception:
        logger.exception("NER failed")
    return out


