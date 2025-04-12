import sys
import os
import pytest
from datetime import date, datetime
# pyright: reportMissingImports=false

# Insert the backend folder into sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services import normalize_individual, safe_strip, normalize_family, parse_date_flexible, extract_events_from_individual, extract_events_from_family

# --- Dummy classes to simulate GEDCOM objects ---

class SubRecord:
    def __init__(self, tag, value=None, sub_records=None):
        self.tag = tag
        self.value = value
        self.sub_records = sub_records or []
    def __repr__(self):
        return f"<SubRecord tag={self.tag} value={self.value}>"

class NameObj:
    def __init__(self, given="", surname=""):
        self.given = given
        self.surname = surname

class RawInd:
    def __init__(self, xref_id, name=None, sub_records=None, name_list=None):
        self.xref_id = xref_id
        self.name = name
        self._name_list = name_list
        self.sub_records = sub_records or []
    def sub_tag_value(self, path):
        parts = path.split("/")
        tag = parts[0]
        subtag = parts[1] if len(parts) > 1 else None
        for sr in self.sub_records:
            if sr.tag == tag:
                if subtag:
                    for ss in sr.sub_records:
                        if ss.tag == subtag:
                            return ss.value
                else:
                    return sr.value
        return None

class RawFam:
    def __init__(self, xref_id, sub_records=None):
        self.xref_id = xref_id
        self.sub_records = sub_records or []
    def sub_tag_value(self, path):
        if path == "MARR/DATE":
            for sr in self.sub_records:
                if sr.tag == "MARR/DATE":
                    return sr.value
        if path == "MARR/PLAC":
            for sr in self.sub_records:
                if sr.tag == "MARR/PLAC":
                    return sr.value
        return None

# --- Tests for safe_strip() ---
@pytest.mark.parametrize("inp,expected", [
    ("  Hello  ", "Hello"),
    (None, ""),
    (["A", "B", ""], "A B"),
    (("X","Y"), "X Y"),
    (123, "123"),
])
def test_safe_strip_various(inp, expected):
    assert safe_strip(inp) == expected

# --- Tests for name parsing ---
def test_name_from_object():
    raw = RawInd("@I1@", name=NameObj("John", "Doe"))
    assert normalize_individual(raw)["name"] == "John Doe"

def test_name_from_list():
    raw = RawInd("@I2@", name=None, name_list=["Alice", "Smith", ""])
    assert normalize_individual(raw)["name"] == "Alice Smith"

def test_name_from_string():
    raw = RawInd("@I3@", name=None, name_list="Charlie McKinley")
    assert normalize_individual(raw)["name"] == "Charlie McKinley"

def test_name_empty_fallback():
    raw = RawInd("@I4@", name=None, name_list=None)
    assert normalize_individual(raw)["name"] == ""

# --- Tests for occupation extraction in normalize_individual() ---

def test_occ_from_occu_tag():
    raw = RawInd("@I5@", name=NameObj("Dora", "Black"), sub_records=[
        SubRecord("OCCU", "Blacksmith")
    ])
    assert normalize_individual(raw)["occupation"] == "Blacksmith"

def test_occ_from_even_type():
    even = SubRecord("EVEN", "Carpenter", sub_records=[SubRecord("TYPE", "Occupation")])
    raw = RawInd("@I6@", name=NameObj("Eli", "Wood"), sub_records=[even])
    assert normalize_individual(raw)["occupation"] == "Carpenter"

def test_occ_from_note_keyword():
    note = SubRecord("NOTE", "Worked as a teacher")
    raw = RawInd("@I7@", name=NameObj("Fay", "Teach"), sub_records=[note])
    occ = normalize_individual(raw)["occupation"]
    assert "teacher" in occ.lower()

def test_occ_from_nested_note():
    # NOTE with nested sub-records containing job info
    nested = SubRecord("NOTE", "Mechanic")
    note = SubRecord("NOTE", "", sub_records=[nested])
    raw = RawInd("@I8@", name=NameObj("Mike", "Wrench"), sub_records=[note])
    occ = normalize_individual(raw)["occupation"]
    assert "mechanic" in occ.lower()

def test_multiple_occu_tags():
    subs = [SubRecord("OCCU", "Teacher"), SubRecord("OCCU", "Janitor")]
    raw = RawInd("@I9@", name=NameObj("Joe", "Worker"), sub_records=subs)
    occ = normalize_individual(raw)["occupation"]
    assert occ in ["Teacher", "Janitor"]

def test_missing_occ_log(capfd):
    raw = RawInd("@I10@", name=NameObj("No", "Job"), sub_records=[])
    normalize_individual(raw)
    out, _ = capfd.readouterr()
    assert "No occupation found for No Job (@I10@)" in out

def test_notes_accumulation():
    notes = [SubRecord("NOTE", "Loves farming"), SubRecord("NOTE", "Carpenter by trade")]
    raw = RawInd("@I11@", name=NameObj("Carl", "Wood"), sub_records=notes)
    result = normalize_individual(raw)
    assert "Loves farming" in result["notes"]
    assert "Carpenter by trade" in result["notes"]

# --- Tests for family normalization ---
def test_normalize_family():
    raw_fam = RawFam("@F1@", sub_records=[
        SubRecord("HUSB", "@I100@"),
        SubRecord("WIFE", "@I101@")
    ])
    fam = normalize_family(raw_fam)
    assert fam["gedcom_id"] == "@F1@"
    assert fam["husband_id"] == "I100"
    assert fam["wife_id"] == "I101"

# --- Tests for event extraction from individual ---
def test_extract_birth_place_only():
    raw = RawInd("@I12@", name=NameObj("Baby", "Doe"), sub_records=[
        SubRecord("BIRT", sub_records=[SubRecord("PLAC", "Detroit")])
    ])
    p = normalize_individual(raw)
    events = extract_events_from_individual(raw, p)
    # Expect one birth event with place only.
    assert len(events) == 1
    event = events[0]
    assert event["location"] == "Detroit"
    assert event["date"] is None
    assert event["date_precision"] == "place_only"

def test_extract_birth_event():
    raw = RawInd("@I13@", name=NameObj("Bart", "Simpson"), sub_records=[
        SubRecord("BIRT", sub_records=[
            SubRecord("DATE", "01 JAN 1900"),
            SubRecord("PLAC", "Springfield")
        ])
    ])
    p = normalize_individual(raw)
    events = extract_events_from_individual(raw, p)
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "birth"
    assert event["date"] == "1900-01-01"
    assert event["location"] == "Springfield"

def test_extract_death_event():
    raw = RawInd("@I14@", name=NameObj("Homer", "Simpson"), sub_records=[
        SubRecord("DEAT", sub_records=[
            SubRecord("DATE", "31 DEC 1950"),
            SubRecord("PLAC", "Shelbyville")
        ])
    ])
    p = normalize_individual(raw)
    events = extract_events_from_individual(raw, p)
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "death"
    assert event["date"] == "1950-12-31"
    assert event["location"] == "Shelbyville"

# --- Tests for event extraction from family ---
def test_extract_marriage_event():
    fam = RawFam("@F2@", sub_records=[
        SubRecord("MARR/DATE", "15 MAR 1920"),
        SubRecord("MARR/PLAC", "Metropolis")
    ])
    events = extract_events_from_family(fam)
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "marriage"
    assert event["date"] == "1920-03-15"
    assert event["location"] == "Metropolis"

def test_family_no_marriage_data():
    fam = RawFam("@F3@", sub_records=[])
    assert extract_events_from_family(fam) == []

# --- Tests for date parsing ---
@pytest.mark.parametrize("date_str,expected", [
    ("01 JAN 1900", date(1900, 1, 1)),
    ("Jan 1900", date(1900, 1, 1)),
    ("1900", date(1900, 1, 1)),
    ("01-01-1900", date(1900, 1, 1)),
    ("1900-01-01", date(1900, 1, 1)),
    ("01/01/1900", date(1900, 1, 1)),
    ("01 January 1900", date(1900, 1, 1)),
    ("January 1900", date(1900, 1, 1)),
    ("Jan. 1, 1900", date(1900, 1, 1)),
    ("January 1, 1900", date(1900, 1, 1)),
])
def test_parse_date_flexible_valid(date_str, expected):
    parsed = parse_date_flexible(date_str)
    assert parsed == expected

def test_parse_date_flexible_invalid():
    assert parse_date_flexible("Not a date") is None
