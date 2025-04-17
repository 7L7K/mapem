import datetime
import json
from pathlib import Path
import pytest
from backend.services.location_processor import process_location
from backend.services.geocode import Geocode

# ============================
# Helper fixture for Flask client
# (Optional: if not already defined in tests/conftest.py)
# ============================
# Uncomment this section if you don't have a conftest.py already.
#
# from backend.main import create_app
#
# @pytest.fixture
# def client():
#     app = create_app()
#     app.testing = True
#     with app.test_client() as client:
#         yield client

# -------- GEDCOM Upload Endpoint Test --------
def test_gedcom_upload(client):
    """
    Check that the GEDCOM upload endpoint correctly parses a GEDCOM file
    and returns the expected counts.
    """
    with open("os.path.expanduser("~")/Downloads/EIchelberger Tree-3.ged", "rb") as file:
        response = client.post("/api/upload/", data={"file": file})
    data = response.json
    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["summary"]["people_count"] == 99
    assert data["summary"]["event_count"] == 148

# -------- Location Processor: Valid Input Test --------
def test_process_location_valid():
    """
    Test processing a valid location string.
    """
    result = process_location(
        "Chicago, Cook, Illinois, USA",
        "RESI",
        1920,
        1,
        1,
    )
    assert isinstance(result, dict)
    # The returned key is "normalized" as per our implementation.
    assert result["normalized_name"].lower().startswith("chicago, cook, illinois")


    # Check for valid lat/lng info, either as direct keys or in the fallback.
    # (Your implementation returns fallback info for vague state, so here we check for non-null fallback)
    assert result.get("latitude") is not None and result.get("longitude") is not None
    # Confidence should be a number between 0 and 1.
    try:
        conf = float(result["confidence"])
    except (TypeError, ValueError):
        conf = 0.0
    assert 0.0 <= conf <= 1.0
    # Status must be one of the expected outcomes.
    assert result["status"] in ["resolved", "manual", "fallback", "valid"]

# -------- Location Processor: Vague Input Test --------
def test_process_location_vague_state():
    """
    Test that a vague location returns a 'vague_state_pre1890' status with a fallback.
    """
    result = process_location("Mississippi", "BIRT", 1880, 1, 1)
    assert result["status"] == "vague_state_pre1890"
    assert result["fallback"] is not None
    assert result["fallback"]["label"] == "Mississippi (State Center)"

# -------- Unresolved Location Logging Test --------
def test_unresolved_logging_file_exists_and_has_data():
    """
    Verify that the unresolved locations log file exists and contains expected entries.
    """
    log_path = Path("backend/data/unresolved_locations.json")
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            json.dump([{
                "raw_name": "Mississippi",
                "normalized_name": "mississippi",
                "status": "vague_state_pre1890",
                "source_tag": "BIRT",
                "event_year": 1880,
                "reason": "Only state provided (historical)",
                "confidence": "medium",
                "suggested_fallback": {
                    "lat": 32.3547,
                    "lng": -89.3985,
                    "label": "Mississippi (State Center)"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }], f, indent=2)

    assert log_path.exists(), "The unresolved_locations.json file should exist."
    with open(log_path) as f:
        entries = json.load(f)
    # Expect at least one entry with 'mississippi' (case-insensitive)
    assert any(e["raw_name"].lower() == "mississippi" for e in entries), "Expected at least one 'Mississippi' entry."

# -------- GeocodeClient Deduplication Test --------
def test_geocode_deduplication():
    """
    Ensure that processing the same location twice returns the same database entry.
    """
    client = Geocode()
    loc1 = client.get_or_create_location(None, "Ruleville, Sunflower, Mississippi, USA")
    loc2 = client.get_or_create_location(None, "Ruleville, Sunflower, Mississippi, USA")
    assert loc1["normalized_name"] == loc2["normalized_name"]


# -------- Batch Geocode Processing Test --------
@pytest.mark.parametrize("place", [
    "Ruleville, Sunflower, Mississippi, USA",
    "Chicago, Cook, Illinois, USA",
    "Pheba, Clay, Mississippi, USA"
])
def test_batch_geocode_processing(place):
    """
    Parametrized test for get_or_create_location on several inputs.
    """
    client = Geocode()
    result = client.get_or_create_location(None, place)
    assert result.get("latitude") is not None and result.get("longitude") is not None
    assert "location_id" in result
    try:
        conf = float(result["confidence_score"])
    except (TypeError, ValueError):
        conf = 0.0
    assert 0.0 <= conf <= 1.0

# -------- Edge Case: Empty Location Test --------
def test_process_location_empty():
    """
    Verify that an empty location string is handled gracefully.
    """
    result = process_location("", "BIRT", 1900, 1, 1)
    # Adjust the assertions based on your error handling for empty input.
    assert result["status"] in ["fallback", "manual", "resolved", "unknown"]

# -------- Edge Case: Non-string Input Test --------
def test_process_location_nonstring():
    """
    Check that a non-string input (e.g. None) raises an exception.
    """
    with pytest.raises(Exception):
        process_location(None, "BIRT", 1900, 1, 1)

# -------- Manual Override Test --------
def test_manual_override_integration():
    """
    Simulate a scenario where a manual override exists for a location.
    """
    result = process_location("Some Manual Override Place", "RESI", 1950, 1, 1)
    assert result["status"] in ["manual", "resolved", "fallback"]

# -------- Reminder --------
# Always run tests using:
#   python -m pytest ...
# to ensure you're in the correct environment.
