import pytest
from backend.services.geocode import Geocode, LocationOut, GeocodeError
from unittest.mock import patch

@pytest.fixture
def geocoder():
    # Force a manual fix for Boliver
    manual_fixes = {
        "boliver_mississippi": {
            "latitude": 33.8,
            "longitude": -90.7,
            "modern_equivalent": "Bolivar County, Mississippi, USA",
        }
    }
    historical_lookup = {
        "beat 2": {
            "latitude": 33.5,
            "longitude": -90.5,
            "modern_equivalent": "Beat 2, Sunflower County, Mississippi",
        }
    }
    return Geocode(
        api_key=None,
        use_cache=False,
        manual_fixes=manual_fixes,
        historical_lookup=historical_lookup
    )

def test_manual_override_hit(geocoder):
    result = geocoder.get_or_create_location(None, "Boliver, Mississippi")
    assert isinstance(result, LocationOut)
    assert result.source == "manual"
    assert result.status == "manual"

@patch("backend.services.geocode.Geocode._nominatim_geocode", return_value=(None, None, None, None, None))
def test_vague_state_classification(mock_geo, geocoder):
    result = geocoder.get_or_create_location(None, "Mississippi")
    assert isinstance(result, GeocodeError)
    assert result.message == "unresolved"

from unittest.mock import patch

@patch("backend.services.geocode.Geocode._nominatim_geocode", return_value=(None, None, None, None, None))
def test_unresolved_logged(mock_geo, geocoder):
    result = geocoder.get_or_create_location(None, "unknown place")
    assert isinstance(result, GeocodeError)
    assert result.message == "unresolved"

def test_geocode_output_structure(geocoder):
    result = geocoder.get_or_create_location(None, "Greenwood, Mississippi")
    if result:
        assert hasattr(result, "raw_name")
        assert hasattr(result, "latitude")
        assert isinstance(result.confidence_score, float)

def test_historical_match_simulated(geocoder):
    result = geocoder.get_or_create_location(None, "Beat 2")
    assert isinstance(result, LocationOut)
    assert result.source == "historical"
