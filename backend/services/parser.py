import logging
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .gedcom_core import GedcomCoreParser
from .gedcom_normalizer import (
    normalize_individual,
    normalize_family,
    extract_events_from_individual,
    extract_events_from_family,
    parse_date_flexible,
)
from ..models import (
    Individual,
    Family,
    TreeRelationship,
    Event,
    Location,
    TreeVersion,
)
from backend.services.location_service import LocationService
from backend.utils.helpers import split_full_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ────────────────────────────────────────────────────────────────
# CONSTANTS
# ────────────────────────────────────────────────────────────────
TAG_CATEGORY_MAP: Dict[str, str] = {
    "BIRT": "life_event",
    "DEAT": "life_event",
    "MARR": "life_event",
    "DIV": "life_event",
    "RESI": "migration",
    "IMMI": "migration",
    "EMIG": "migration",
    "CENS": "migration",
}

FANOUT_TAGS = {"MARR", "DIV"}


# ────────────────────────────────────────────────────────────────
# PARSER CLASS
# ────────────────────────────────────────────────────────────────
class GEDCOMParser:
    """End‑to‑end pipeline: **read GEDCOM → normalise → persist**.

    A single instance is *stateful*: you call :py:meth:`parse_file` exactly once,
    then :py:meth:`save_to_db`.  A fresh instantiation is cheap if you need to
    process multiple files.
    """

    def __init__(self, file_path: str, location_service: LocationService):
        self.file_path = file_path
        self.location_service = location_service
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        logger.debug("Initialized GEDCOMParser for %s", file_path)

    # ═══════════════════════════════════════════════════════════
    # FILE PARSING
    # ═══════════════════════════════════════════════════════════
    def parse_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse *once* and cache the result in :pyattr:`data`."""
        t0 = datetime.now()
        logger.info("📂 Starting parse of %s", self.file_path)

        core = GedcomCoreParser(self.file_path)
        raw = core.parse()  # returns nested dicts/lists
        logger.debug("Raw parse finished in %.2fs", (datetime.now() - t0).total_seconds())

        individuals, families, events = [], [], []

        # 1️⃣ Individuals -----------------------------------------------------------------
        for raw_ind in raw.get("individuals", []):
            norm = normalize_individual(raw_ind)
            individuals.append(norm)

            evts = extract_events_from_individual(raw_ind, norm)
            for evt in evts:
                tag = (evt.get("source_tag") or "").upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")
            events.extend(evts)
        logger.info("👤 Parsed %d individuals → %d individual‑level events", len(individuals), len(events))

        # 2️⃣ Families --------------------------------------------------------------------
        for raw_fam in raw.get("families", []):
            fam_norm = normalize_family(raw_fam)
            families.append(fam_norm)

            fam_evts_all = extract_events_from_family(raw_fam, fam_norm)
            fam_evts_keep = []
            for evt in fam_evts_all:
                tag = (evt.get("source_tag") or "").upper()
                evt["category"] = TAG_CATEGORY_MAP.get(tag, "unspecified")

                # fan‑out marriage/divorce to spouses
                if tag in FANOUT_TAGS:
                    for spouse in (fam_norm.get("husband_id"), fam_norm.get("wife_id")):
                        if spouse:
                            indiv_evt = evt.copy()
                            indiv_evt["individual_gedcom_id"] = spouse
                            events.append(indiv_evt)
                    continue  # skip family‑level record
                fam_evts_keep.append(evt)
            events.extend(fam_evts_keep)
        logger.info("🏠 Parsed %d families — total events: %d", len(families), len(events))

        # Cache & return
        self.data = {
            "individuals": individuals,
            "families": families,
            "events": events,
        }
        logger.debug("parse_file() complete in %.2fs", (datetime.now() - t0).total_seconds())
        return self.data

    # ═══════════════════════════════════════════════════════════
    # DATABASE WRITE
    # ═══════════════════════════════════════════════════════════
    def save_to_db(
        self,
        session: Session,
        uploaded_tree_id: UUID,
        tree_version_id: Optional[UUID] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Write normalised data.

        The caller must supply an open SQLAlchemy :pyclass:`Session` that will be
        **committed or rolled‑back here**.  If *dry_run* is ``True`` we always
        roll back so that nothing is persisted (handy for tests).
        """
        if not self.data:
            raise RuntimeError("parse_file() has to be called before save_to_db()")

        logger.info("💾 save_to_db(uploaded_tree_id=%s, version_id=%s, dry=%s)", uploaded_tree_id, tree_version_id, dry_run)
        summary = {"people_count": 0, "event_count": 0, "warnings": [], "errors": []}

        # ── TreeVersion --------------------------------------------------
        if not tree_version_id:
            tree_version = TreeVersion(uploaded_tree_id=uploaded_tree_id, version_number=1)
            session.add(tree_version)
            session.flush()
            tree_version_id = tree_version.id
            logger.debug("Created new TreeVersion %s", tree_version_id)
        else:
            logger.debug("Using existing TreeVersion %s", tree_version_id)

        # ── Individuals --------------------------------------------------
        individuals = self.data.get("individuals", [])
        logger.debug("Persisting %d individuals", len(individuals))
        for ind in individuals:
            gedcom_id = ind.get("gedcom_id")
            if not ind.get("name"):
                warn = f"Missing name for {gedcom_id} — skipped"
                logger.warning(warn)
                summary["warnings"].append(warn)
                continue

            first_name, last_name = split_full_name(ind["name"])
            occupation = ind.get("occupation") or None

            existing = (
                session.query(Individual)
                .filter_by(gedcom_id=gedcom_id, tree_id=tree_version_id)
                .first()
            )
            if existing:
                existing.first_name = first_name
                existing.last_name = last_name
                existing.occupation = occupation
            else:
                session.add(
                    Individual(
                        gedcom_id=gedcom_id,
                        first_name=first_name,
                        last_name=last_name,
                        occupation=occupation,
                        tree_id=tree_version_id,
                    )
                )
                summary["people_count"] += 1

        self._flush(session, summary, "Individuals")
        ged2db = {p.gedcom_id: p.id for p in session.query(Individual).filter_by(tree_id=tree_version_id)}

        # ── Families & Relationships ------------------------------------
        families = self.data.get("families", [])
        logger.debug("Persisting %d families", len(families))
        for fam in families:
            fam_id = fam.get("gedcom_id")
            h_id = ged2db.get(fam.get("husband_id"))
            w_id = ged2db.get(fam.get("wife_id"))

            existing_fam = (
                session.query(Family)
                .filter_by(gedcom_id=fam_id, tree_id=tree_version_id)
                .first()
            )
            if existing_fam:
                existing_fam.husband_id = h_id
                existing_fam.wife_id = w_id
            else:
                session.add(Family(gedcom_id=fam_id, husband_id=h_id, wife_id=w_id, tree_id=tree_version_id))

            # parent‑child edges -----------------------------------------
            for child_ged in fam.get("children", []):
                child_db_id = ged2db.get(child_ged)
                if child_db_id:
                    if h_id:
                        session.add(TreeRelationship(tree_id=uploaded_tree_id, person_id=h_id, related_person_id=child_db_id, relationship_type="father"))
                    if w_id:
                        session.add(TreeRelationship(tree_id=uploaded_tree_id, person_id=w_id, related_person_id=child_db_id, relationship_type="mother"))

        self._flush(session, summary, "Families & Relationships")

        # ── Events & Locations ------------------------------------------
        events = self.data.get("events", [])
        logger.debug("Persisting %d events", len(events))
        for evt in events:
            if not evt.get("event_type"):
                warn = "Missing event_type — skipped event"
                summary["warnings"].append(warn)
                logger.warning(warn)
                continue

            location_id = self._resolve_location(session, evt, uploaded_tree_id)  # may be None
            date_obj = parse_date_flexible(evt["date"]) if evt.get("date") else None

            ev = Event(
                event_type=evt.get("event_type", "UNKNOWN"),
                date=date_obj,
                date_precision=evt.get("date_precision"),
                notes=evt.get("notes"),
                source_tag=evt.get("source_tag"),
                category=evt.get("category", "unspecified"),
                location_id=location_id,  # ← NULLable, we *keep* the event even if unresolved
                tree_id=tree_version_id,
            )

            # participant link ------------------------------------------
            if (ind_ged := evt.get("individual_gedcom_id")) and (ind_db := ged2db.get(ind_ged)):
                person = session.get(Individual, ind_db)
                if person:
                    ev.participants.append(person)

            session.add(ev)
            summary["event_count"] += 1

        logger.info("📝 About to commit: %s people, %s events (TreeVersion %s)", summary["people_count"], summary["event_count"], tree_version_id)

        # ── Commit / rollback ------------------------------------------
        if dry_run:
            session.rollback()
            logger.info("⚙️ Dry‑run complete — rolled back transactions")
        else:
            session.commit()
            logger.info("✅ Committed TreeVersion %s", tree_version_id)
        return summary

    # ────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ────────────────────────────────────────────────────────────
    def _flush(self, session: Session, summary: Dict[str, Any], label: str) -> None:
        try:
            session.flush()
            logger.debug("✔️ Flush OK after %s", label)
        except Exception as exc:
            msg = f"Flush failed after {label}: {exc}"
            summary["errors"].append(msg)
            logger.exception(msg)
            raise

    def _resolve_location(self, session: Session, evt: Dict[str, Any], uploaded_tree_id: UUID) -> Optional[int]:
        """Return *Location.id* **or** ``None`` if the place cannot be resolved."""
        place = evt.get("location") or evt.get("place")
        if not place:
            return None

        year: Optional[int] = None
        if evt.get("date"):
            if dt := parse_date_flexible(evt["date"]):
                year = dt.year

        loc_out = self.location_service.resolve_location(
            raw_place=place,
            event_year=year,
            source_tag=evt.get("source_tag", ""),
            tree_id=uploaded_tree_id,
        )
        if not loc_out:
            logger.warning("⚠️ Location not resolved: '%s' (year=%s)", place, year)
            return None

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
            logger.debug("🗺️ Added new Location '%s'", loc_out.normalized_name)
        return loc.id
