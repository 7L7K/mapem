from __future__ import annotations

import hashlib
import io
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage

from backend.db import SessionLocal
from backend.models import Source, IndividualSource, EventSource, Event, Individual
from backend.utils.debug_routes import debug_route
from backend.services.ml_assists import ocr_extract_hints

media_routes = Blueprint("media", __name__, url_prefix="/api/media")


def _hash_file(file: FileStorage) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: file.stream.read(8192), b""):
        h.update(chunk)
    file.stream.seek(0)
    return h.hexdigest()


@media_routes.route("/upload", methods=["POST"])
@debug_route
def upload_media():
    """Attach a media file to an Event or Individual and OCR its text.

    Form fields:
      - file: binary
      - event_id | individual_id: UUID
      - description: optional
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "missing file"}), 400

    description = request.form.get("description") or ""
    event_id = request.form.get("event_id")
    individual_id = request.form.get("individual_id")

    if not event_id and not individual_id:
        return jsonify({"error": "event_id or individual_id required"}), 400

    db = SessionLocal()
    try:
        # compute content hash
        doc_hash = _hash_file(file)

        # extract small text preview for OCR (if text-like)
        text_content: Optional[dict] = None
        try:
            # naive attempt; real OCR would decode image/PDF
            buf = file.read()
            file.stream.seek(0)
            sample = buf[:2000].decode("utf-8", errors="ignore")
            hints = ocr_extract_hints(sample)
            text_content = {"sample": sample[:500], "hints": hints}
        except Exception:
            text_content = None

        source = Source(
            source_type="media",
            description=description,
            url="",  # TODO: integrate real storage and set URL
            document_hash=doc_hash,
            text_content=text_content,
        )
        db.add(source)
        db.flush()

        if event_id:
            # ensure event exists
            evt = db.get(Event, event_id)
            if not evt:
                return jsonify({"error": "event not found"}), 404
            link = EventSource(event_id=evt.id, source_id=source.id, confidence=1.0)
            db.add(link)
        if individual_id:
            person = db.get(Individual, individual_id)
            if not person:
                return jsonify({"error": "individual not found"}), 404
            link = IndividualSource(individual_id=person.id, source_id=source.id)
            db.add(link)

        db.commit()
        return jsonify({
            "source_id": source.id,
            "document_hash": doc_hash,
            "hints": text_content.get("hints") if text_content else [],
        }), 201
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return jsonify({"error": "internal"}), 500
    finally:
        try:
            db.close()
        except Exception:
            pass


