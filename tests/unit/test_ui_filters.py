# tests/unit/test_filters.py
import pytest
from backend.services.filters import normalize_filters, _normalise_checkbox_input

# ─────────────────────────────────────────────────────────────
# low-level helper that was returning too early
# ─────────────────────────────────────────────────────────────
def test_normalise_checkbox_input_handles_multiple_true_dict_keys():
    raw = {"birth": True, "death": True, "residence": False}
    cleaned = _normalise_checkbox_input(raw, {"birth", "death", "residence"})
    assert set(cleaned) == {"birth", "death"}

# ─────────────────────────────────────────────────────────────
# public API – guard-rails
# ─────────────────────────────────────────────────────────────
def test_normalize_filters_year_defaults_and_cleaning():
    payload = {"eventTypes": ["Birth", "DeAtH"], "yearRange": [None, None]}
    out = normalize_filters(payload)

    # eventTypes are lower-cased & validated
    assert out["eventTypes"] == ["birth", "death"]

    # year defaults applied
    assert out["year"]["min"] == 1700
    assert out["year"]["max"] >= 2025   # current year

def test_normalize_filters_rejects_bad_type():
    with pytest.raises(TypeError):
        normalize_filters("not-a-dict")          # type: ignore[arg-type]
