# os.path.expanduser("~")/mapem/backend/services/gedcom_normalizer.py
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 1) Flexible date parser (unchanged)
def parse_date_flexible(date_str):
    """
    Accepts strings or DateValue* objects.
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()
    formats = [
        "%d %b %Y",      # 01 JAN 1900
        "%b %Y",         # JAN 1900
        "%Y",            # 1900
        "%d-%m-%Y",      # 01-01-1900
        "%Y-%m-%d",      # 1900-01-01
        "%d/%m/%Y",      # 01/01/1900
        "%d %B %Y",      # 01 January 1900
        "%B %Y",         # January 1900
        "%b. %d, %Y",    # Jan. 1, 1900
        "%B %d, %Y"      # January 1, 1900
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except Exception:
            continue
    return None

# 2) Safe strip helper (unchanged)
def safe_strip(value):
    if isinstance(value, (list, tuple)):
        return " ".join([str(v) for v in value if v]).strip()
    return str(value).strip() if value else ""

# 3) Map of GEDCOM tags → (event_type, category)
EVENT_TAGS = {
    "BIRT": ("birth", "life_event"),
    "DEAT": ("death", "life_event"),
    "BAPM": ("baptism", "religious_event"),
    "CHR":  ("christening", "religious_event"),
    "BURI": ("burial", "life_event"),
    "CENS": ("census", "census"),
    "EMIG": ("emigration", "migration"),
    "IMMI": ("immigration", "migration"),
    "MARR": ("marriage", "family_event"),
    "DIV":  ("divorce", "family_event"),
    "ADOP": ("adoption", "family_event"),
    # add more as needed...
}

def normalize_family(family_record):
    fam_id = family_record.xref_id
    husb_id = wife_id = None
    for sub in family_record.sub_records:
        if sub.tag == "HUSB" and sub.value:
            husb_id = sub.value.strip('@')
        elif sub.tag == "WIFE" and sub.value:
            wife_id = sub.value.strip('@')
    return {
        "gedcom_id": fam_id,
        "husband_id": husb_id,
        "wife_id": wife_id,
        "extra_details": {}
    }

def extract_events_from_individual(individual_record, normalized_individual, counters=None):
    events = []
    gid = normalized_individual.get("gedcom_id")

    def _track(key):
        if counters is not None:
            counters[key] = counters.get(key, 0) + 1

    # —— 3) Loop through every tag in EVENT_TAGS —— 
    for tag, (etype, category) in EVENT_TAGS.items():
        date_raw  = individual_record.sub_tag_value(f"{tag}/DATE")
        place_raw = individual_record.sub_tag_value(f"{tag}/PLAC")

        date_obj  = parse_date_flexible(str(date_raw)) if date_raw else None
        place     = place_raw or None

        if date_obj or place:
            # precision logic
            if date_obj and place:
                precision = "exact"
            elif date_obj:
                precision = "date_only"
            else:
                precision = "place_only"

            _track(f"{etype}_{precision}")

            events.append({
                "event_type": etype,
                "individual_gedcom_id": gid,
                "date": date_obj.isoformat() if date_obj else None,
                "date_precision": precision,
                "notes": "",
                "location": place,
                "source_tag": tag,
                "category": category
            })

    return events

def extract_events_from_family(family_record, normalized_family, counters=None):
    """
    Returns a list of family‐level events (marriage, divorce, separation),
    each linked back to the husband and wife via gedcom IDs.
    """
    events = []
    fam_id    = normalized_family["gedcom_id"]
    husb_id   = normalized_family.get("husband_id")
    wife_id   = normalized_family.get("wife_id")

    def _track(key):
        if counters is not None:
            counters[key] = counters.get(key, 0) + 1

    # Helper to pull date/place
    def _get(tag):
        raw_date  = family_record.sub_tag_value(f"{tag}/DATE")
        raw_place = family_record.sub_tag_value(f"{tag}/PLAC")
        date_obj  = parse_date_flexible(str(raw_date)) if raw_date else None
        place     = raw_place or None
        return date_obj, place

    # --- Marriage ---
    marr_date, marr_place = _get("MARR")
    if marr_date or marr_place:
        precision = (
            "exact"       if marr_date and marr_place else
            "date_only"   if marr_date else
            "place_only"
        )
        _track(f"family_marr_{precision}")
        events.append({
            "event_type":        "marriage",
            "family_gedcom_id":  fam_id,
            "husband_gedcom_id": husb_id,
            "wife_gedcom_id":    wife_id,
            "date":              marr_date.isoformat() if marr_date else None,
            "date_precision":    precision,
            "location":          marr_place,
            "source_tag":        "MARR",
            "category":          "family_event",
            "notes":             ""
        })

    # --- Divorce ---
    div_date, div_place = _get("DIV")
    if div_date or div_place:
        precision = (
            "exact"     if div_date and div_place else
            "date_only" if div_date else
            "place_only"
        )
        _track(f"family_div_{precision}")
        events.append({
            "event_type":        "divorce",
            "family_gedcom_id":  fam_id,
            "husband_gedcom_id": husb_id,
            "wife_gedcom_id":    wife_id,
            "date":              div_date.isoformat() if div_date else None,
            "date_precision":    precision,
            "location":          div_place,
            "source_tag":        "DIV",
            "category":          "family_event",
            "notes":             ""
        })

    # --- Separation (SEPR) ---
    sepr_date, sepr_place = _get("SEPR")
    if sepr_date or sepr_place:
        precision = (
            "exact"      if sepr_date and sepr_place else
            "date_only"  if sepr_date else
            "place_only"
        )
        _track(f"family_sepr_{precision}")
        events.append({
            "event_type":        "separation",
            "family_gedcom_id":  fam_id,
            "husband_gedcom_id": husb_id,
            "wife_gedcom_id":    wife_id,
            "date":              sepr_date.isoformat() if sepr_date else None,
            "date_precision":    precision,
            "location":          sepr_place,
            "source_tag":        "SEPR",
            "category":          "family_event",
            "notes":             ""
        })

    return events


def normalize_individual(raw_ind):
    # —— 1) Name parsing —— 
    name = ""
    if hasattr(raw_ind, "name") and raw_ind.name:
        given   = getattr(raw_ind.name, "given", "") or ""
        surname = getattr(raw_ind.name, "surname", "") or ""
        try:
            name = " ".join([str(p) for p in (given, surname) if p]).strip()
        except Exception:
            name = ""
    else:
        raw_name = raw_ind.sub_tag_value("NAME") or getattr(raw_ind, "_name_list", None)
        if isinstance(raw_name, (list, tuple)):
            name = " ".join([str(p) for p in raw_name if p]).strip()
        else:
            name = (str(raw_name) or "").strip()

    person = {
        "gedcom_id": raw_ind.xref_id,
        "name":      name,
        "occupation": "",
        "notes":     ""
    }
    got_job = False

    # —— 2) Occupation & notes scanning —— 
    for sub in getattr(raw_ind, "sub_records", []):
        tag = sub.tag
        val = safe_strip(sub.value) if sub.value else ""

        if tag == "OCCU" and val:
            person["occupation"] = val
            got_job = True

        elif tag == "EVEN":
            ev_type = raw_ind.sub_tag_value("EVEN/TYPE") or ""
            if "occupation" in ev_type.lower() and val and not got_job:
                person["occupation"] = val
                got_job = True
            if val:
                person["notes"] += val + " "

        elif tag == "NOTE":
            if val:
                low = val.lower()
                if any(k in low for k in ["farmer", "laborer", "teacher", "clerk", "servant", "pastor", "minister", "engineer", "cook", "driver"]):
                    if not got_job:
                        person["occupation"] = val
                        got_job = True
                person["notes"] += val + " "
            for note_sub in getattr(sub, "sub_records", []):
                nval = safe_strip(note_sub.value) if note_sub.value else ""
                low = nval.lower()
                if any(k in low for k in ["farmer", "laborer", "teacher", "clerk", "servant", "pastor", "minister", "engineer", "cook", "driver"]):
                    if not got_job:
                        person["occupation"] = nval
                        got_job = True
                if nval:
                    person["notes"] += nval + " "

    if not got_job:
        logger.info(
            "🕵️ No occupation found for %s (%s)",
            person['name'],
            person['gedcom_id'],
        )

    return person
