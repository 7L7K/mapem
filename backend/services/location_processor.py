#os.path.expanduser("~")/mapem/backend/services/location_processor.py
import os
import json
import re
from datetime import datetime

# ─── Manual Overrides & Historical Mappings ────────────────────────────────

# Use os.path.join correctly. Here, we expect the manual fixes file to live at:
# os.path.expanduser("~")/mapem/backend/data/manual_place_fixes.json
MANUAL_FIXES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "manual_place_fixes.json")
try:
    with open(MANUAL_FIXES_PATH, "r") as f:
        MANUAL_FIXES = json.load(f)
    # Normalize keys using our helper below
    def normalize_string(s):
        s = s.strip().lower()
        s = re.sub(r'\s+', ' ', s)
        s = re.sub(r',+', ',', s)
        s = re.sub(r'(, )+', ',', s)
        return s.strip(", ")
    MANUAL_FIXES = { normalize_string(k): v for k, v in MANUAL_FIXES.items() }
except Exception as e:
    MANUAL_FIXES = {}
    print(f"Warning: Could not load manual fixes: {e}")

# Historical mappings directory: expects files in os.path.expanduser("~")/mapem/data/historical_places
HISTORICAL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "historical_places")

def load_historical_mapping(filename):
    path = os.path.join(HISTORICAL_DIR, filename)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load historical mapping {filename}: {e}")
        return {}

# Example: load one mapping; extend this as needed.
HISTORICAL_MAPPING = load_historical_mapping("sunflower_beats_1910.json")

# ─── Normalization Functions ───────────────────────────────────────────────

def normalize_location(raw):
    """Clean up the raw location string."""
    norm = raw.strip()
    norm = re.sub(r"\s+", " ", norm)
    norm = norm.replace(" ,", ",").replace(",,", ",").strip(", ")
    # Remove trailing USA-related words
    norm = re.sub(r"\b(united states of america|usa)\b", "", norm, flags=re.IGNORECASE).strip(", ")
    
    # 🧽 Remove repeated segments (like 'Beat 2, Beat 2')
    parts = [p.strip() for p in norm.split(",")]
    deduped = []
    for i, part in enumerate(parts):
        if i == 0 or part.lower() != parts[i - 1].lower():
            deduped.append(part)
    norm = ", ".join(deduped)

    return norm

# ─── Classification Functions ──────────────────────────────────────────────

def classify_location(normalized, event_year=None):
    """
    Classify the location using heuristics.
    Returns: (normalized, status, note, confidence)
    
    Status values:
      - valid: complete location info
      - vague_state_pre1890: only state provided and event_year < 1890
      - vague_state_modern: only state provided and event_year >= 1890
      - historical: beat-level or legacy info detected
      - unknown: insufficient data
    """
    lowered = normalized.lower()
    # Define set of state-only names (adjust as needed)
    state_only = {"mississippi", "arkansas", "alabama", "tennessee", "louisiana"}
    if lowered in state_only:
        if event_year and event_year < 1890:
            return normalized, "vague_state_pre1890", "Only state provided (historical)", "medium"
        else:
            return normalized, "vague_state_modern", "Only state provided (modern)", "medium"
    
    # Historical beat detection: if it starts with "beat" and mentions Mississippi
    if re.match(r"^beat \d+.*mississippi", lowered):
        # If we have a historical mapping match (exact match in the mapping)
        if normalized in HISTORICAL_MAPPING:
            return normalized, "historical", "Matched historical mapping", "high"
        return normalized, "historical", "Beat-level location in Mississippi", "high"
    
    # Standard valid if it has at least 3 parts (e.g., City, County, State)
    parts = [p.strip() for p in normalized.split(",")]
    if len(parts) >= 3:
        return normalized, "valid", "Standard format", "high"
    
    # If it has two parts, assume it might be city/state
    if len(parts) == 2:
        return normalized, "valid", "Assumed city/state format", "medium"
    
    return normalized, "unknown", "Insufficient data", "low"

def apply_manual_overrides(normalized):
    """Override based on manual fixes if available."""
    if normalized in MANUAL_FIXES:
        fixed = MANUAL_FIXES[normalized]
        return fixed, "manual_override", f"Manual override to {fixed}", "high"
    return normalized, None, None, None

# ─── Core Processing Function ───────────────────────────────────────────────

def process_location(raw, source_tag="", event_year=None):
    """
    Process a raw location string:
      - Normalize the string
      - Apply manual overrides (if any)
      - Classify based on heuristics and event_year
      - Optionally attempt historical matching
    Returns a dictionary with:
      normalized, status, note, confidence, and fallback (if applicable)
    """
    norm = normalize_location(raw)
    
    # 1) Check for manual overrides first
    fixed, override_status, override_note, override_conf = apply_manual_overrides(norm)
    print(f"🌀 [PROCESS_LOCATION] Raw: '{raw}' → Normalized: '{norm}'")
    if override_status:
        print(f"🔁 [MANUAL OVERRIDE] '{norm}' → '{fixed}' ({override_note})")
        return {
            "normalized": fixed,
            "status": override_status,
            "note": override_note,
            "confidence": override_conf,
            "fallback": None
        }
        
    # 2) Classify the location
    norm, status, note, confidence = classify_location(norm, event_year=event_year)
    
    # 3) For vague state-only entries, suggest a fallback (e.g., state center coordinates)
    fallback = None
    if status in ["vague_state_pre1890", "vague_state_modern"]:
        # Example fallback: Mississippi state center; adjust per state if needed.
        fallback = {
            "lat": 32.3547,
            "lng": -89.3985,
            "label": f"{norm} (State Center)"
        }
    
    return {
        "normalized": norm,
        "status": status,
        "note": note,
        "confidence": confidence,
        "fallback": fallback
    }

# ─── Unresolved Logging Functions ────────────────────────────────────────────

def create_unresolved_entry(raw, processed, event_year, event_id, source_tag, tree_id=3, version_id=3, person_id=None):
    """Create a record for an unresolved location."""
    return {
        "tree_id": tree_id,
        "version_id": version_id,
        "event_id": event_id,
        "person_id": person_id,
        "raw_name": raw,
        "normalized_name": processed["normalized"],
        "status": processed["status"],
        "source_tag": source_tag,
        "event_year": event_year,
        "reason": processed["note"],
        "confidence": processed["confidence"],
        "suggested_fallback": processed["fallback"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def log_unresolved_location(entry):
    # Define the unresolved log file path; adjust as needed
    unresolved_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "unresolved_locations.json")
    print(f"🗂️ Logging to: {unresolved_file_path}")
    try:
        if os.path.exists(unresolved_file_path):
            with open(unresolved_file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️ Unresolved file was empty or invalid. Starting fresh.")
                    data = []
        else:
            data = []
        data.append(entry)
        print(f"📝 [UNRESOLVED_LOG] {entry['raw_name']} → {entry['status']}")
        print(f"📦 Total unresolved entries: {len(data)}")
        with open(unresolved_file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Error logging unresolved location: {e}")

# ─── End of Module ───────────────────────────────────────────────────────────
