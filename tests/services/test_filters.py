import pytest
from backend.services.filters import normalize_filters


def test_normalize_basic_event_filters():
    raw = {
        "eventTypes": ["birth", "DEATH", "invalid"],
        "year": {"min": 1850, "max": 1920},
        "vague": True,
        "sources": ["census", "manual", None],
    }

    result = normalize_filters(raw)

    assert result["eventTypes"] == ["birth", "death"]  # normalized + filtered
    assert result["year"] == {"min": 1850, "max": 1920}
    assert result["vague"] is True
    assert result["sources"] == ["census", "manual"]


def test_normalize_rejects_extra_keys():
    raw = {
        "eventTypes": ["birth"],
        "extraKey": "trash",
    }

    with pytest.raises(ValueError, match="Invalid filter keys: extraKey"):
        normalize_filters(raw)


def test_normalize_empty_values():
    raw = {
        "eventTypes": [],
        "sources": None,
        "vague": False,
        "year": {},
    }

    result = normalize_filters(raw)

    assert result["eventTypes"] == []
    assert result["sources"] == []
    assert result["vague"] is False
    assert result["year"] == {"min": 1700, "max": 2025}  # fallback behavior


def test_normalize_invalid_input_types():
    with pytest.raises(TypeError, match="filters payload must be a JSON object"):
        normalize_filters("not a dict")
