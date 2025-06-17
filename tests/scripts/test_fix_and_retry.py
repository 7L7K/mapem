import json
import tempfile
from pathlib import Path
from backend.services.geocode import Geocode, LocationOut
from backend.utils.helpers import normalize_location


def test_apply_manual_fixes_on_mock_data(tmp_path):
    # Simulate unresolved_locations.json file
    unresolved_data = [
        {
            "raw_name": "Ackerman, Choctaw, Mississippi, USA",
            "source_tag": "gedcom",
            "timestamp": "2025-05-15T00:00:00",
            "reason": "geocode_failed",
            "status": "manual_fix_pending",
            "suggested_fix": None
        },
        {
            "raw_name": "Mississippi",
            "source_tag": "gedcom",
            "timestamp": "2025-05-15T00:00:00",
            "reason": "vague",
            "status": "manual_fix_pending",
            "suggested_fix": None
        }
    ]

    unresolved_path = tmp_path / "unresolved_locations.json"
    with open(unresolved_path, "w") as f:
        json.dump(unresolved_data, f)

    # Simulate manual_place_fixes.json
    fixes = {
        "ackerman_choctaw_mississippi_usa": {
            "modern_equivalent": "Ackerman, Mississippi, USA",
            "lat": 33.3037,
            "lng": -89.1723
        }
    }
    manual_fixes_path = tmp_path / "manual_place_fixes.json"
    with open(manual_fixes_path, "w") as f:
        json.dump(fixes, f)

    # Run Geocode with test files
    fixes = {
        "ackerman_choctaw_mississippi_usa": {
            "modern_equivalent": "Ackerman, Mississippi, USA",
            "lat": 33.3037,
            "lng": -89.1723
        }
    }
    manual_fixes_path = tmp_path / "manual_place_fixes.json"
    with open(manual_fixes_path, "w") as f:
        json.dump(fixes, f)

    geo = Geocode(use_cache=False, manual_fixes=fixes)
    geo.cache_file = str(tmp_path / "test_cache.json")

    # Inject the test fix via JSON loading
    with open(manual_fixes_path, encoding="utf-8") as f:
        manual_fixes = json.load(f)

    norm_name = normalize_location("Ackerman, Choctaw, Mississippi, USA")
    assert norm_name in manual_fixes

    result = geo.get_or_create_location(None, "Ackerman, Choctaw, Mississippi, USA")
    assert isinstance(result, LocationOut)
    assert result.confidence_label == "manual"
    assert result.latitude == 33.3037
