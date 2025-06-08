from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_date_flexible(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        "%d %b %Y", "%b %Y", "%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y",
        "%d %B %Y", "%B %Y", "%b. %d, %Y", "%B %d, %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except Exception:
            continue
    return None

def safe_strip(value):
    if isinstance(value, (list, tuple)):
        return " ".join([str(v) for v in value if v]).strip()
    return str(value).strip() if value else ""

EVENT_TAGS = {
    "BIRT": ("birth",        "life_event"),
    "DEAT": ("death",        "life_event"),
    "BURI": ("burial",       "life_event"),
    "MARR": ("marriage",     "family_event"),
    "DIV":  ("divorce",      "family_event"),
    "SEPR": ("separation",   "family_event"),
    "ADOP": ("adoption",     "family_event"),
    "BAPM": ("baptism",      "religious_event"),
    "CHR":  ("christening",  "religious_event"),
    "CENS": ("census",       "census"),
    "RESI": ("residence",    "life_event"),
    "EMIG": ("emigration",   "migration"),
    "IMMI": ("immigration",  "migration"),
    "EVEN": ("custom_event", "other"),
    "OCCU": ("occupation",   "biography")
}

def normalize_individual(raw_ind):
    name = ""
    if hasattr(raw_ind, "name") and raw_ind.name:
        given = getattr(raw_ind.name, "given", "") or ""
        surname = getattr(raw_ind.name, "surname", "") or ""
        name = " ".join([str(p) for p in (given, surname) if p]).strip()
    else:
        raw_name = raw_ind.sub_tag_value("NAME") or getattr(raw_ind, "_name_list", None)
        if isinstance(raw_name, (list, tuple)):
            name = " ".join([str(p) for p in raw_name if p]).strip()
        else:
            name = (str(raw_name) or "").strip()

    # Add name suffix
    suffix = raw_ind.sub_tag_value("NSFX")
    if suffix:
        name = f"{name} {suffix.strip()}"

    person = {
        "gedcom_id": raw_ind.xref_id,
        "name": name,
        "occupation": "",
        "notes": ""
    }

    got_job = False

    for sub in getattr(raw_ind, "sub_records", []):
        tag = sub.tag
        val = safe_strip(sub.value) if sub.value else ""

        # Combine all child text from CONC/CONT
        def _flatten_text(record):
            parts = [safe_strip(record.value or "")]
            for sr in getattr(record, "sub_records", []):
                if sr.tag in ("CONC", "CONT"):
                    parts.append(safe_strip(sr.value))
            return " ".join(parts).strip()

        if tag == "OCCU":
            full_val = _flatten_text(sub)
            if full_val:
                person["occupation"] = full_val
                got_job = True

        elif tag == "NOTE":
            full_note = _flatten_text(sub)
            if full_note:
                low = full_note.lower()
                if any(k in low for k in ["farmer", "laborer", "teacher", "clerk", "servant", "pastor", "minister", "engineer", "cook", "driver"]):
                    if not got_job:
                        person["occupation"] = full_note
                        got_job = True
                person["notes"] += full_note + " "

        elif tag == "EVEN":
            ev_type = raw_ind.sub_tag_value("EVEN/TYPE") or ""
            if "occupation" in ev_type.lower() and val and not got_job:
                person["occupation"] = val
                got_job = True
            if val:
                person["notes"] += val + " "

    if not got_job:
        logger.info("🕵️ No occupation found for %s (%s)", person["name"], person["gedcom_id"])

    return person

def extract_events_from_individual(individual_record, normalized_individual, counters=None):
    events = []
    gid = normalized_individual.get("gedcom_id")

    def _track(key):
        if counters is not None:
            counters[key] = counters.get(key, 0) + 1

    for tag, (etype, category) in EVENT_TAGS.items():
        date_raw = individual_record.sub_tag_value(f"{tag}/DATE")
        place_raw = individual_record.sub_tag_value(f"{tag}/PLAC")
        date_obj = parse_date_flexible(str(date_raw)) if date_raw else None
        place = place_raw or None

        # Collect source info
        source_info = []
        for sub in individual_record.sub_records:
            if sub.tag == tag:
                for ss in sub.sub_records:
                    if ss.tag in ("SOUR", "PAGE", "TITL"):
                        source_info.append(f"{ss.tag}: {safe_strip(ss.value)}")

        if date_obj or place:
            precision = (
                "exact" if date_obj and place else
                "date_only" if date_obj else
                "place_only"
            )
            _track(f"{etype}_{precision}")
            events.append({
                "event_type": etype,
                "individual_gedcom_id": gid,
                "date": date_obj.isoformat() if date_obj else None,
                "date_precision": precision,
                "notes": "; ".join(source_info) if source_info else "",
                "location": place,
                "source_tag": tag,
                "category": category
            })

    return events

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

def extract_events_from_family(family_record, normalized_family, counters=None):
    events = []
    fam_id = normalized_family["gedcom_id"]
    husb_id = normalized_family.get("husband_id")
    wife_id = normalized_family.get("wife_id")

    def _track(key):
        if counters is not None:
            counters[key] = counters.get(key, 0) + 1

    def _get(tag):
        raw_date = family_record.sub_tag_value(f"{tag}/DATE")
        raw_place = family_record.sub_tag_value(f"{tag}/PLAC")
        date_obj = parse_date_flexible(str(raw_date)) if raw_date else None
        place = raw_place or None
        return date_obj, place

    for tag in ["MARR", "DIV", "SEPR"]:
        if tag in EVENT_TAGS:
            event_type, category = EVENT_TAGS[tag]
            date, place = _get(tag)
            if date or place:
                precision = (
                    "exact" if date and place else
                    "date_only" if date else
                    "place_only"
                )
                _track(f"family_{event_type}_{precision}")
                events.append({
                    "event_type": event_type,
                    "family_gedcom_id": fam_id,
                    "husband_gedcom_id": husb_id,
                    "wife_gedcom_id": wife_id,
                    "date": date.isoformat() if date else None,
                    "date_precision": precision,
                    "location": place,
                    "source_tag": tag,
                    "category": category,
                    "notes": ""
                })

    return events
