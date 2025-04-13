# File: backend/parser.py

from datetime import datetime
from .gedcom_core import GedcomCoreParser
from .gedcom_normalizer import (
    normalize_individual,
    normalize_family,
    extract_events_from_individual,
    extract_events_from_family,
    parse_date_flexible,
)
# ✅ RIGHT
from ..models import Individual, Family, TreeRelationship, Event, Location
from app.utils.helpers import normalize_location_name
from sqlalchemy.orm import Session
# near the top of parser.py
import logging
logger = logging.getLogger(__name__)

# Tag → category map (unchanged)
TAG_CATEGORY_MAP = {
    "BIRT": "life_event",
    "DEAT": "life_event",
    "MARR": "life_event",
    "DIV":  "life_event",
    "RESI": "migration",
    "IMMI": "migration",
    "EMIG": "migration",
    "CENS": "migration",
    # ... etc
}

def get_or_create_location(session: Session, place_raw: str):
    """Ensure a Location row exists for this place string, return its ID."""
    if not place_raw:
        return None

    normalized = normalize_location_name(place_raw)
    loc = session.query(Location).filter_by(normalized_name=normalized).first()
    if not loc:
        loc = Location(
            name=place_raw.strip(),
            normalized_name=normalized,
            latitude=None,
            longitude=None,
            confidence_score=None,
        )
        session.add(loc)
        session.flush()  # get loc.id
    return loc.id

class GEDCOMParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {}
        self.event_quality_counts = {}

    def parse_file(self):
        core = GedcomCoreParser(self.file_path)
        raw = core.parse()

        individuals, families, events = [], [], []

        # Individuals + their events
        for raw_ind in raw["individuals"]:
            norm = normalize_individual(raw_ind)
            individuals.append(norm)

            evts = extract_events_from_individual(raw_ind, norm)
            for evt in evts:
                tag = evt["source_tag"].upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
            events.extend(evts)

        # Families + their events
        for raw_fam in raw["families"]:
            fam_norm = normalize_family(raw_fam)
            families.append(fam_norm)

            fam_evts = extract_events_from_family(raw_fam, fam_norm)
            for evt in fam_evts:
                tag = evt["source_tag"].upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
            events.extend(fam_evts)

        self.data = {
            "individuals": individuals,
            "families": families,
            "events": events,
        }
        return self.data

    def save_to_db(self, session: Session, tree_id: int, geocode_client=None, dry_run=False):
        """
        Inserts Individuals, Families, Relationships, and Events.
        If geocode_client provided, any evt["location"] will be geocoded & linked.
        """
        data = self.data
        summary = {"people_count":0, "event_count":0, "warnings":[], "errors":[]}

        # 1) Individuals
        for ind in data["individuals"]:
            gedcom_id = ind["gedcom_id"]
            existing = session.query(Individual).filter_by(gedcom_id=gedcom_id, tree_id=tree_id).first()
            if existing:
                existing.name = ind["name"]
                existing.occupation = ind["occupation"]
                existing.notes = ind["notes"]
            else:
                person = Individual(
                    gedcom_id=gedcom_id,
                    name=ind["name"],
                    occupation=ind["occupation"],
                    notes=ind["notes"],
                    tree_id=tree_id
                )
                session.add(person)
                summary["people_count"] += 1
        session.flush()

        # build GEDCOM → DB ID map
        ged2db = {
            p.gedcom_id: p.id
            for p in session.query(Individual).filter_by(tree_id=tree_id)
        }

        # 2) Families & Relationships
        for fam in data["families"]:
            fam_id = fam["gedcom_id"]
            raw_h, raw_w = fam.get("husband_id"), fam.get("wife_id")
            h_id, w_id = ged2db.get(raw_h), ged2db.get(raw_w)

            existing_fam = session.query(Family).filter_by(gedcom_id=fam_id, tree_id=tree_id).first()
            if existing_fam:
                existing_fam.husband_id = h_id  # type: ignore[attr-defined]
                existing_fam.wife_id   = w_id  # type: ignore[attr-defined]
            else:
                f = Family(
                    gedcom_id=fam_id,
                    husband_id=h_id,
                    wife_id=w_id,
                    tree_id=tree_id
                )
                session.add(f)
            # parent-child edges
            for child_ged in fam.get("children", []):
                child_db = ged2db.get(child_ged)
                if h_id is not None and child_db is not None:
                    session.add(TreeRelationship(
                        tree_id=tree_id,
                        person_id=h_id,
                        related_person_id=child_db,
                        relationship_type="father"
                    ))
                if w_id is not None and child_db is not None:
                    session.add(TreeRelationship(
                        tree_id=tree_id,
                        person_id=w_id,
                        related_person_id=child_db,
                        relationship_type="mother"
                    ))
        session.flush()

        # 3) Events (with location extraction + geocoding)
        for evt in data["events"]:
            # parse date
            dt = parse_date_flexible(evt.get("date")) if evt.get("date") else None
            e = Event(
                event_type=evt["event_type"],
                date=dt,
                date_precision=evt["date_precision"],
                notes=evt["notes"],
                source_tag=evt["source_tag"],
                category=evt["category"],
                tree_id=tree_id
            )
            # link individual/family
            if "individual_gedcom_id" in evt:
                e.individual_id = ged2db.get(evt["individual_gedcom_id"])  # type: ignore[attr-defined]
            if "family_gedcom_id" in evt:
                # assume you build fam2db similarly if you need family events
                pass

            # LOCATION HANDLING
            place = evt.get("location") or evt.get("place")
            if place:
                loc_id = get_or_create_location(session, place)

                if geocode_client and loc_id is not None:
                    lat, lon, norm_name, conf = geocode_client.get_or_create_location(session, place)
                    loc = session.query(Location).get(loc_id)
                    if loc is not None:
                        loc.latitude         = lat
                        loc.longitude        = lon
                        loc.confidence_score = conf
                        session.add(loc)
                        logger.debug(f"📍 Linked event to geocoded location: {place} → ID {loc_id}")
                else:
                    logger.debug(f"📍 No geocode client, linking to raw location: {place} → ID {loc_id}")

                e.location_id = loc_id  # type: ignore[attr-defined]

            session.add(e)
            summary["event_count"] += 1

        session.flush()
        if dry_run:
            session.rollback()
        return summary
