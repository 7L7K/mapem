import pytest
from sqlalchemy import text
from backend.db import SessionLocal

@pytest.mark.db
def test_geolocated_events_have_coordinates():
    """Ensure events have valid location data: lat/lng, or at least marked vague."""

    session = SessionLocal()
    try:
        # ── Step 1: Get latest tree_id by created_at ──
        tree_row = session.execute(text("""
            SELECT id FROM tree_versions
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()

        assert tree_row, "❌ No tree_versions found in DB"
        tree_id = tree_row[0]

        # ── Step 2: Query all events and their geolocation status ──
        result = session.execute(text("""
            SELECT e.id, e.event_type, l.normalized_name, l.latitude, l.longitude, l.status
            FROM events e
            LEFT JOIN locations l ON e.location_id = l.id
            WHERE e.tree_id = :tree_id
        """), {"tree_id": tree_id})

        rows = result.fetchall()
        total_events = len(rows)

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

        # ── Step 3: Output ──
        print(f"\n📍 Tree ID: {tree_id}")
        print(f"📦 Total Events: {total_events}")
        print(f"🚨 Missing Coordinates: {len(missing_coords)}")
        print(f"🕳️ Vague Locations: {len(vague)}")

        if missing_coords:
            print("\n⚠️ Events missing lat/lng (top 10 shown):")
            for r in missing_coords[:10]:
                print(f" - ID: {r['event_id']}, type: {r['event_type']}, place: '{r['place']}', status: {r['status']}")

        # ── Step 4: Assertions ──
        assert total_events > 0, "No events found for the latest tree"
        assert len(missing_coords) == 0, f"{len(missing_coords)} events missing lat/lng"

    finally:
        session.close()
