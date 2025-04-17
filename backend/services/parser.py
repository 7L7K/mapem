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

            fam_evts = extract_events_from_family(raw_fam, fam_norm)
            for evt in fam_evts:
                tag = evt.get("source_tag", "").upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
            events.extend(fam_evts)

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
        All location resolution is handled by self.location_service.

        :param session: SQLAlchemy session
        :param tree_id: Which tree we're inserting into
        :param dry_run: If True, will rollback at the end instead of committing
        :return: summary dict with counts & warnings
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

            existing = session.query(Individual).filter_by(gedcom_id=gedcom_id, tree_id=tree_id).first()
            if existing:
                existing.name = ind.get("name")
                existing.occupation = ind.get("occupation")
                existing.notes = ind.get("notes")
            else:
                person = Individual(
                    gedcom_id=gedcom_id,
                    name=ind.get("name", "Unknown"),
                    occupation=ind.get("occupation"),
                    notes=ind.get("notes"),
                    tree_id=tree_id
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

        # Build a map of gedcom_id -> db_id for Individuals
        ged2db = {
            p.gedcom_id: p.id
            for p in session.query(Individual).filter_by(tree_id=tree_id)
        }

        # --- 2) Insert/Update Families & Relationships ---
        for fam in data.get("families", []):
            fam_id = fam.get("gedcom_id")
            raw_h, raw_w = fam.get("husband_id"), fam.get("wife_id")
            h_id = ged2db.get(raw_h)
            w_id = ged2db.get(raw_w)

            existing_fam = session.query(Family).filter_by(gedcom_id=fam_id, tree_id=tree_id).first()
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

            # Parent-child relationships
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

        # --- 3) Insert Events + Resolve Locations ---
        for evt in data.get("events", []):
            place = evt.get("location") or evt.get("place")
            location_id = None

            if place:
                # Print debugging info
                print(f"\n🌍 [LOCATION RAW] Tag: {evt.get('source_tag', '')} | '{place}'")

                # Attempt to parse an event year from the date
                event_year = None
                if evt.get("date"):
                    try:
                        dt = parse_date_flexible(evt["date"])
                        event_year = dt.year if dt else None
                    except Exception:
                        event_year = None

                # Use our location_service to resolve the location
                loc_out: LocationOut = self.location_service.resolve_location(
                    raw_place=place,
                    event_year=event_year,
                    source_tag=evt.get("source_tag", "")
                )

                print("   ➡ [RESOLVED]\n", loc_out.model_dump_json(indent=2))


                # Check if we already have this normalized_name in DB
                loc = session.query(Location).filter_by(normalized_name=loc_out.normalized_name).first()
                if not loc:
                    loc = Location(
                        raw_name=loc_out.raw_name,
                        name=loc_out.normalized_name,
                        normalized_name=loc_out.normalized_name,
                        latitude=loc_out.latitude,
                        longitude=loc_out.longitude,
                        confidence_score=loc_out.confidence_score,
                        status=loc_out.status,
                        source=loc_out.source
                    )
                    session.add(loc)
                    session.flush()
                location_id = loc.id

            # Validate event_type
            if not evt.get("event_type"):
                logger.warning(f"Skipping event missing event_type: {evt}")
                summary["warnings"].append("Missing event_type in an event")
                continue

            dt = parse_date_flexible(evt.get("date")) if evt.get("date") else None
            e = Event(
                event_type=evt.get("event_type", "UNKNOWN"),
                date=dt,
                date_precision=evt.get("date_precision"),
                notes=evt.get("notes"),
                source_tag=evt.get("source_tag"),
                category=evt.get("category", "unspecified"),
                tree_id=tree_id
            )

            # Link to an individual if present
            if evt.get("individual_gedcom_id"):
                e.individual_id = ged2db.get(evt["individual_gedcom_id"])

            # (Optional) Link to a family if you want
            if evt.get("family_gedcom_id"):
                # You could set e.family_id = some reference if you store family events
                pass

            # Attach the location if found/resolved
            if location_id:
                e.location_id = location_id

            session.add(e)
            summary["event_count"] += 1

        # Attempt final flush
        try:
            session.flush()
        except Exception as e:
            logger.error(f"Flush failed after inserting Events: {e}")
            summary["errors"].append("Flush error after events")
            if not dry_run:
                raise

        # Print summary
        print("\n📊 Insert Summary:")
        print("   Individuals added:", summary["people_count"])
        print("   Events added:", summary["event_count"])
        print("   Warnings:", len(summary["warnings"]))

        # If dry_run, rollback changes so DB doesn't retain them
        if dry_run:
            session.rollback()
            logger.info("Dry run mode: transaction rolled back.")

        return summary
