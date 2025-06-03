from backend.utils.event_helpers import primary_participant

class DummyInd:
    def __init__(self, id, first_name, last_name, role=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.role = role

class DummyEvent:
    def __init__(self, participants):
        self.participants = participants
        self.id = 999

def test_empty_event_returns_unknown():
    event = DummyEvent([])
    assert primary_participant(event) == (-1, "Unknown")

def test_first_strategy_returns_first():
    p1, p2 = DummyInd(1, "A", "B"), DummyInd(2, "C", "D")
    event = DummyEvent([p1, p2])
    assert primary_participant(event, strategy="first") == (1, "A B")

def test_named_strategy_skips_blank():
    blank = DummyInd(3, "", "")          # no name
    named = DummyInd(4, "Ella", "Fitz")
    event = DummyEvent([blank, named])
    assert primary_participant(event, strategy="named") == (4, "Ella Fitz")

def test_with_role_strategy_fallback():
    bride = DummyInd(5, "Tina", "Turner", role="bride")
    groom = DummyInd(6, "Ike", "Turner", role="groom")
    event = DummyEvent([groom, bride])
    # Should pick bride first
    assert primary_participant(event, strategy="with_role:bride") == (5, "Tina Turner")
    # Unknown role → default to first (groom)
    assert primary_participant(event, strategy="with_role:officiant") == (6, "Ike Turner")
