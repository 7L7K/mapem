#os.path.expanduser("~")/mapem/backend/services/parser.py
import logging
from sqlalchemy.orm import Session

from .gedcom_core import GedcomCoreParser
from .gedcom_normalizer import (
    normalize_individual,
    normalize_family,
    extract_events_from_individual,
    extract_events_from_family,
    parse_date_flexible,
)
from ..models import Individual, Family, TreeRelationship, Event, Location
from backend.services.location_service import LocationService
from backend.models.location_models import LocationOut
from backend.utils.helpers import split_full_name



logger = logging.getLogger(__name__)

# Tag → category map
TAG_CATEGORY_MAP = {
    "BIRT": "life_event",
    "DEAT": "life_event",
    "MARR": "life_event",
    "DIV":  "life_event",
    "RESI": "migration",
    "IMMI": "migration",
    "EMIG": "migration",
    "CENS": "migration",
    # ... etc ...
}


class GEDCOMParser:
    def __init__(self, file_path: str, location_service: LocationService):
        """
        :param file_path: Path to the GEDCOM file to parse
        :param location_service: An injected LocationService instance
        """
        self.file_path = file_path
        self.location_service = location_service
        self.data = {}  # will hold { "individuals": [...], "families": [...], "events": [...] }

    def parse_file(self):
        """
        Parse the GEDCOM file into normalized dictionaries for individuals, families, and events.
        """
        core = GedcomCoreParser(self.file_path)
        raw = core.parse()  # { "individuals": [...], "families": [...], ... }

        individuals, families, events = [], [], []

        # 1) Process Individuals + their events
        for raw_ind in raw.get("individuals", []):
            # Basic normalization for individual
            norm = normalize_individual(raw_ind)
            individuals.append(norm)

            # Extract events from the individual's data
            evts = extract_events_from_individual(raw_ind, norm)
            for evt in evts:
                tag = evt.get("source_tag", "").upper()
                # If tag is recognized, set category, else "unspecified"
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
            events.extend(evts)

        # 2) Process Families + their events
        for raw_fam in raw.get("families", []):
            fam_norm = normalize_family(raw_fam)
            families.append(fam_norm)

# Existing: add event with only family_id
            fam_evts = extract_events_from_family(raw_fam, fam_norm)
            fanout_tags = {"MARR", "DIV"}           # tags that should exist only as individual events
            fam_evts_keep = []                      # ← events we will actually retain

            for evt in fam_evts:
                tag = evt.get("source_tag", "").upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
                # --- PATCH START ---
                # For marriage/divorce/etc., attach to BOTH spouses as individual events!
                if tag in fanout_tags:
                    for spouse in (fam_norm.get("husband_id"), fam_norm.get("wife_id")):
                        if spouse:
                            indiv_evt = evt.copy()
                            indiv_evt["individual_gedcom_id"] = spouse
                            events.append(indiv_evt)
                    continue
                else: 
                    fam_evts_keep.append(evt)
                # --- PATCH END ---
            events.extend(fam_evts_keep)

        # Store the processed data internally
        self.data = {
            "individuals": individuals,
            "families": families,
            "events": events,
        }
        return self.data
    def save_to_db(self, session: Session, tree_id: int, dry_run=False):
        """
        Inserts Individuals, Families, Relationships, and Events into the DB.
        """
        data = self.data
        summary = {"people_count": 0, "event_count": 0, "warnings": [], "errors": []}

        # --- 1) Insert/Update Individuals ---
        for ind in data.get("individuals", []):
            gedcom_id = ind.get("gedcom_id")
            if not ind.get("name"):
                logger.warning(f"Skipping individual with missing name: {gedcom_id}")
                summary["warnings"].append(f"Missing name for individual {gedcom_id}")
                continue

            first_name, last_name = split_full_name(ind.get("name", "Unknown"))
            occupation = ind.get("occupation") or None

            existing = session.query(Individual).filter_by(
                gedcom_id=gedcom_id,
                tree_id=tree_id
            ).first()

            if existing:
                existing.first_name  = first_name
                existing.last_name   = last_name
                existing.occupation  = occupation
            else:
                person = Individual(
                    gedcom_id=gedcom_id,
                    first_name=first_name,
                    last_name=last_name,
                    occupation=occupation,
                    tree_id=tree_id,
                )
                session.add(person)
                summary["people_count"] += 1

        try:
            session.flush()
        except Exception as e:
            logger.error(f"Flush failed after inserting Individuals: {e}")
            summary["errors"].append("Flush error after individuals")
            if not dry_run:
                raise

        ged2db = {p.gedcom_id: p.id for p in session.query(Individual).filter_by(tree_id=tree_id)}

        # --- 2) Insert/Update Families & Relationships ---
        for fam in data.get("families", []):
            fam_id = fam.get("gedcom_id")
            raw_h, raw_w = fam.get("husband_id"), fam.get("wife_id")
            h_id = ged2db.get(raw_h)
            w_id = ged2db.get(raw_w)

            existing_fam = session.query(Family).filter_by(
                gedcom_id=fam_id,
                tree_id=tree_id
            ).first()

            if existing_fam:
                existing_fam.husband_id = h_id
                existing_fam.wife_id = w_id
            else:
                f = Family(
                    gedcom_id=fam_id,
                    husband_id=h_id,
                    wife_id=w_id,
                    tree_id=tree_id
                )
                session.add(f)

            for child_ged in fam.get("children", []):
                child_db_id = ged2db.get(child_ged)
                if h_id and child_db_id:
                    session.add(TreeRelationship(
                        tree_id=tree_id,
                        person_id=h_id,
                        related_person_id=child_db_id,
                        relationship_type="father"
                    ))
                if w_id and child_db_id:
                    session.add(TreeRelationship(
                        tree_id=tree_id,
                        person_id=w_id,
                        related_person_id=child_db_id,
                        relationship_type="mother"
                    ))

        try:
            session.flush()
        except Exception as e:
            logger.error(f"Flush failed after inserting Families/Relationships: {e}")
            summary["errors"].append("Flush error after families")
            if not dry_run:
                raise

        # --- 3) Insert Events + Resolve Locations (with M2M) ---
        for evt in data.get("events", []):
            if not evt.get("event_type"):
                logger.warning(f"Skipping event missing event_type: {evt}")
                summary["warnings"].append("Missing event_type in an event")
                continue

            place = evt.get("location") or evt.get("place")
            location_id = None
            if place:
                event_year = None
                if evt.get("date"):
                    try:
                        dt = parse_date_flexible(evt["date"])
                        if dt:
                            event_year = dt.year
                    except Exception:
                        pass

                loc_out = self.location_service.resolve_location(
                    raw_place=place,
                    event_year=event_year,
                    source_tag=evt.get("source_tag", ""),
                    tree_id=tree_id,
                )

                loc = session.query(Location).filter_by(normalized_name=loc_out.normalized_name).first()
                if not loc:
                    loc = Location(
                        raw_name=loc_out.raw_name,
                        normalized_name=loc_out.normalized_name,
                        latitude=loc_out.latitude,
                        longitude=loc_out.longitude,
                        confidence_score=loc_out.confidence_score,
                        status=loc_out.status,
                        source=loc_out.source,
                    )
                    session.add(loc)
                    session.flush()
                location_id = loc.id

            dt = parse_date_flexible(evt.get("date")) if evt.get("date") else None
            e = Event(
                event_type=evt.get("event_type", "UNKNOWN"),
                date=dt,
                date_precision=evt.get("date_precision"),
                notes=evt.get("notes"),
                source_tag=evt.get("source_tag"),
                category=evt.get("category", "unspecified"),
                tree_id=tree_id,
                location_id=location_id
            )

            # --- 🔥 Attach participants (M2M) ---
            individual_gedcom_id = evt.get("individual_gedcom_id")
            if individual_gedcom_id:
                indiv_db_id = ged2db.get(individual_gedcom_id)
                if indiv_db_id:
                    individual = session.get(Individual, indiv_db_id)
                    if individual:
                        e.participants.append(individual)
                    else:
                        logger.warning(f"Individual {individual_gedcom_id} not found in DB.")
                else:
                    logger.warning(f"No DB ID found for GEDCOM ID {individual_gedcom_id}.")

            session.add(e)
            summary["event_count"] += 1

        if not dry_run:
            try:
                session.commit()
            except Exception as e:
                logger.error(f"Commit failed: {e}")
                summary["errors"].append(f"Commit failed: {str(e)}")
                raise
        else:
            session.rollback()

        # Proactive: Always return summary, even if zero events
        return summary
