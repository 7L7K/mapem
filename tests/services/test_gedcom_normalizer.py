# tests/services/test_gedcom_normalizer.py
import pytest
from datetime import date

from backend.services.gedcom_normalizer import (
    parse_date_flexible,
    normalize_individual,
    extract_events_from_individual,
    normalize_family,
    extract_events_from_family,
)

class DummyRecord:
    def __init__(self, xref_id="I1", name=None, sub_records=None):
        self.xref_id = xref_id
        self.name = name
        self.sub_records = sub_records or []

    def sub_tag_value(self, tag_path):
        parts = tag_path.split("/")
        for sub in self.sub_records:
            if sub.tag == parts[0]:
                if len(parts) == 1:
                    return sub.value
                for subsub in sub.sub_records:
                    if subsub.tag == parts[1]:
                        return subsub.value
        return None

class DummyName:
    def __init__(self, given="", surname=""):
        self.given = given
        self.surname = surname

class SubRecord:
    def __init__(self, tag, value=None, sub_records=None):
        self.tag = tag
        self.value = value
        self.sub_records = sub_records or []

# ─────────────────────────────────────────────────────────────
# 🔍 Test parse_date_flexible
# ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("input_str,expected", [
    ("01 JAN 1900", date(1900, 1, 1)),
    ("Jan. 1, 1900", date(1900, 1, 1)),
    ("1900", date(1900, 1, 1)),
    ("", None),
    (None, None),
    ("invalid", None),
])
def test_parse_date_flexible(input_str, expected):
    assert parse_date_flexible(input_str) == expected

# ─────────────────────────────────────────────────────────────
# 👤 Test normalize_individual
# ─────────────────────────────────────────────────────────────
def test_normalize_individual_name_and_occupation():
    sub_records = [
        SubRecord("OCCU", "farmer"),
        SubRecord("NOTE", "he was a good farmer"),
    ]
    dummy = DummyRecord(
        xref_id="I123",
        name=DummyName("John", "Doe"),
        sub_records=sub_records
    )
    norm = normalize_individual(dummy)
    assert norm["name"] == "John Doe"
    assert norm["occupation"] == "farmer"
    assert "good farmer" in norm["notes"]

# ─────────────────────────────────────────────────────────────
# 🧠 Test extract_events_from_individual
# ─────────────────────────────────────────────────────────────
def test_extract_events_from_individual_basic():
    sub_records = [
        SubRecord("BIRT", None, [SubRecord("DATE", "01 JAN 1900"), SubRecord("PLAC", "Mississippi")]),
        SubRecord("DEAT", None, [SubRecord("DATE", "2000"), SubRecord("PLAC", "Chicago")]),
    ]
    dummy = DummyRecord(xref_id="I999", name=DummyName("Jane", "Smith"), sub_records=sub_records)
    norm = normalize_individual(dummy)
    events = extract_events_from_individual(dummy, norm)
    assert len(events) == 2
    assert events[0]["event_type"] == "birth"
    assert events[1]["event_type"] == "death"

# ─────────────────────────────────────────────────────────────
# ❤️ Test family normalization
# ─────────────────────────────────────────────────────────────
def test_normalize_family_and_events():
    sub_records = [
        SubRecord("HUSB", "@I1@"),
        SubRecord("WIFE", "@I2@"),
        SubRecord("MARR", None, [SubRecord("DATE", "1890"), SubRecord("PLAC", "Canton")]),
        SubRecord("DIV", None, [SubRecord("DATE", "1920")]),
        SubRecord("SEPR", None, [SubRecord("PLAC", "Jackson")]),
    ]
    fam = DummyRecord(xref_id="F1", sub_records=sub_records)
    norm = normalize_family(fam)
    events = extract_events_from_family(fam, norm)
    assert len(events) == 3
    assert events[0]["event_type"] == "marriage"
    assert events[1]["event_type"] == "divorce"
    assert events[2]["event_type"] == "separation"
