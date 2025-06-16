import json
import pytest
from pathlib import Path

from backend.services.location_service import LocationService
from backend.models.location_models import LocationOut

@pytest.fixture(autouse=True)
def data_files(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "manual_place_fixes.json").write_text(json.dumps({
        "manualtown_mt": {"lat": 1.0, "lng": 2.0}
    }))
    hist_dir = data_dir / "historical_places"
    hist_dir.mkdir()
    (hist_dir / "hist.json").write_text(json.dumps({
        "oldplace_op": {"lat": 3.0, "lng": 4.0}
    }))
    monkeypatch.setenv("MAPEM_DATA_DIR", str(data_dir))
    # update loaded tables
    import backend.services.location_processor as lp
    lp.MANUAL_FIXES = {"manualtown_mt": {"lat": 1.0, "lng": 2.0}}
    lp.HISTORICAL_LOOKUP = {"oldplace_op": (3.0, 4.0, "oldplace_op")}

@pytest.fixture
def svc(monkeypatch):
    class DummyGeo:
        def get_or_create_location(self, _s, place):
            if "lowtown" in place.lower():
                return LocationOut(
                    raw_name=place,
                    normalized_name="lowtown_lt",
                    latitude=5.0,
                    longitude=6.0,
                    confidence_score=0.3,
                    confidence_label="api",
                    status="ok",
                    source="api",
                )
            return None
    monkeypatch.setattr("backend.services.location_service.Geocode", lambda *a, **k: DummyGeo())
    return LocationService(mock_mode=True)


def test_manual_hit(svc):
    out = svc.resolve_location("ManualTown, MT", event_year=1900)
    assert out.status == "manual"
    assert out.source == "manual"


def test_historical_hit(svc):
    out = svc.resolve_location("OldPlace, OP", event_year=1800)
    assert out.status == "historical"


def test_vague_input(svc):
    out = svc.resolve_location("Mississippi", event_year=1950)
    assert out.status == "vague"
    assert out.confidence_label == "low"


def test_unresolved_case(svc):
    out = svc.resolve_location("Unknownville", event_year=2000)
    assert out.status == "unresolved"


def test_low_confidence_api_hit(svc):
    out = svc.resolve_location("LowTown, LT", event_year=2000)
    assert out.source == "api"
    assert out.confidence_score == 0.3


def test_mock_mode(svc, monkeypatch):
    called = {}
    class BoomGeo:
        def get_or_create_location(self, *_a, **_k):
            called['hit'] = True
            return None
    monkeypatch.setattr("backend.services.location_service.Geocode", lambda *a, **k: BoomGeo())
    local = LocationService(mock_mode=True)
    local.resolve_location("NoApiTown")
    assert called.get('hit') is None

