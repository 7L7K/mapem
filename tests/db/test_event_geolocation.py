"""Database snapshot tests.

These tests require a pre-populated database snapshot and will be skipped
unless the environment variable ``RUN_DB_SNAPSHOTS`` is set to ``1``.
"""

import os
import logging
import pytest
from sqlalchemy import text
import backend.db as db

# ── Skip if not explicitly enabled ──
if os.environ.get("RUN_DB_SNAPSHOTS") != "1":
    pytest.skip(
        "Skipping DB snapshot tests; set RUN_DB_SNAPSHOTS=1 to run",
        allow_module_level=True,
    )


@pytest.mark.db
def test_geolocated_events_have_coordinates():
    """Ensure events have valid location data: lat/lng, or at least are marked vague."""

    session = db.SessionLocal()
    try:
        # ── Step 1: Get latest tree_id by creation time ──
        tree_row = session.execute(text("""
            SELECT id FROM tree_versions
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()

        assert tree_row, "❌ No tree_versions found in DB"
        tree_id = tree_row[0]

        # ── Step 2: Query events + joined location info ──
        result = session.execute(text("""
            SELECT e.id, e.event_type, l.normalized_name, l.latitude, l.longitude, l.status
            FROM events e
            LEFT JOIN locations l ON e.location_id = l.id
            WHERE e.tree_id = :tree_id
        """), {"tree_id": tree_id})

        rows = result.fetchall()
        total_events = len(rows)

        # ── Step 3: Evaluate rows ──
        missing_coords = []
        for r in rows:
            if not r.latitude or not r.longitude:
                missing_coords.append({
                    "event_id": r.id,
                    "event_type": r.event_type,
                    "place": r.normalized_name,
                    "status": r.status
                })

        vague = [r for r in rows if r.status in ("vague", "vague_state_pre1890")]

        # ── Step 4: Log debug info ──
        logger = logging.getLogger(__name__)
        logger.info("Tree ID: %s", tree_id)
        logger.info("Total Events: %s", total_events)
        logger.info("Missing Coordinates: %s", len(missing_coords))
        logger.info("Vague Locations: %s", len(vague))

        if missing_coords:
            logger.info("Events missing lat/lng (top 10 shown):")
            for r in missing_coords[:10]:
                logger.info(
                    " - ID: %s, type: %s, place: '%s', status: %s",
                    r["event_id"], r["event_type"], r["place"], r["status"]
                )

        # ── Step 5: Assertions ──
        assert total_events > 0, "No events found for the latest tree"
        assert len(missing_coords) == 0, f"{len(missing_coords)} events missing lat/lng"

    finally:
        session.close()
