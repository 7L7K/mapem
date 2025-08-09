#/Users/kingal/mapem/backend/services/parser.py
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

 
from backend.utils.logger import get_file_logger

logger = get_file_logger("parser")

# ...rest of your imports and code...


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
                            # 📝 Fan-out log
                            logger.info(f"🔁 FAN-OUT {tag} → gedcom_id {spouse}")
                    continue  # skip family‑level record
                fam_evts_keep.append(evt)
            events.extend(fam_evts_keep)

        # 📝 Summary after parsing
        logger.info(
            "✅ parse_file done: %d individuals, %d families, %d raw events",
            len(individuals), len(families), len(events)
        )
        self.data = {
            "individuals": individuals,
            "families": families,
            "events": events,
        }
        logger.debug("parse_file() complete in %.2fs", (datetime.now() - t0).total_seconds())
        return self.data

    def save_to_db(
        self,
        session: Session,
        uploaded_tree_id: Optional[UUID] = None,
        tree_version_id: Optional[UUID] = None,
        dry_run: bool = False,
        *,
        tree_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Write normalised data.

        Parameters
        ----------
        session : Session
            Open database session (transaction handled by caller).
        uploaded_tree_id : UUID | None
            Identifier of :class:`UploadedTree`.
        tree_version_id : UUID | None
            Existing tree version or ``None`` to create a new one.
        dry_run : bool
            If ``True`` no changes will be committed.
        tree_id : UUID | None
            Back-compat parameter. If this matches an existing TreeVersion.id,
            it will be treated as ``tree_version_id``. Otherwise it's treated
            as an ``uploaded_tree_id``.
        """
        # Backwards compatibility: "tree_id" may refer to TreeVersion.id or UploadedTree.id
        if tree_id is not None:
            # If explicit uploaded_tree_id is also provided and conflicts, bail
            if uploaded_tree_id is not None and tree_version_id is None:
                # If both provided, prefer explicit tree_version_id; else they must agree
                try:
                    # best-effort compare to existing version's upload id
                    existing_version = session.get(TreeVersion, tree_id)
                    if existing_version and existing_version.uploaded_tree_id != uploaded_tree_id:
                        raise ValueError("Conflicting tree identifiers provided")
                except Exception:
                    # If not a valid UUID or not found, fall through
                    pass
            # Try treat as TreeVersion first
            existing = session.get(TreeVersion, tree_id)
            if existing is not None:
                tree_version_id = existing.id
                uploaded_tree_id = existing.uploaded_tree_id
            else:
                # Treat as uploaded tree id
                uploaded_tree_id = tree_id
        if not self.data:
            raise RuntimeError("parse_file() has to be called before save_to_db()")

        logger.info("💾 save_to_db(uploaded_tree_id=%s, version_id=%s, dry=%s)", uploaded_tree_id, tree_version_id, dry_run)
        summary = {"people_count": 0, "event_count": 0, "warnings": [], "errors": []}

        # ── TreeVersion --------------------------------------------------
        if not tree_version_id:
            # Determine next version number for this uploaded tree
            last = (
                session.query(TreeVersion.version_number)
                .filter(TreeVersion.uploaded_tree_id == uploaded_tree_id)
                .order_by(TreeVersion.version_number.desc())
                .first()
            )
            next_version = (last[0] + 1) if last else 1
            tree_version = TreeVersion(uploaded_tree_id=uploaded_tree_id, version_number=next_version)
            session.add(tree_version)
            session.flush()
            tree_version_id = tree_version.id
            logger.info(f"🌳 New TreeVersion {tree_version_id}")
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
                logger.info(f"+Individual {existing.id} (gedcom {gedcom_id}) [UPDATED]")
            else:
                new_ind = Individual(
                    gedcom_id=gedcom_id,
                    first_name=first_name,
                    last_name=last_name,
                    occupation=occupation,
                    tree_id=tree_version_id,
                )
                session.add(new_ind)
                session.flush()
                logger.info(f"+Individual {new_ind.id} (gedcom {gedcom_id})")
                summary["people_count"] += 1

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
                logger.info(f"+Family {existing_fam.id}")
            else:
                new_fam = Family(gedcom_id=fam_id, husband_id=h_id, wife_id=w_id, tree_id=tree_version_id)
                session.add(new_fam)
                session.flush()
                logger.info(f"+Family {new_fam.id}")
            # parent‑child edges
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
                warn = "⛔ Skipped event: Missing event_type"
                summary["warnings"].append(warn)
                logger.warning(warn)
                continue

            # Reasonable bad date skip
            bad_date = False
            date_str = evt.get("date")
            if date_str and not parse_date_flexible(date_str):
                warn = f"⛔ Skipped event: Bad date '{date_str}'"
                summary["warnings"].append(warn)
                logger.warning(warn)
                bad_date = True
            if bad_date:
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
                location_id=location_id,
                tree_id=tree_version_id,
            )

            if (ind_ged := evt.get("individual_gedcom_id")) and (ind_db := ged2db.get(ind_ged)):
                person = session.get(Individual, ind_db)
                if person:
                    ev.participants.append(person)

            # 📝 Log every event before adding
            logger.info(
                f"+Event {ev.event_type}@{ev.date} → loc={location_id} | participant_ged={evt.get('individual_gedcom_id')}"
            )

            # ── Duplicate check ─────────────────────────────
            participants_ids = {p.id for p in ev.participants}
            duplicates = []
            for cand in session.query(Event).filter_by(
                tree_id=tree_version_id,
                event_type=ev.event_type,
                date=ev.date,
                location_id=location_id,
            ).all():
                if {p.id for p in cand.participants} == participants_ids:
                    duplicates.append(cand)

            if duplicates:
                logger.info(
                    "↩️ Duplicate event ignored for participants %s", participants_ids
                )
                continue

            session.add(ev)
            summary["event_count"] += 1

        logger.info(
            "📝 Finished preparing: %s people, %s events (TreeVersion %s)",
            summary["people_count"],
            summary["event_count"],
            tree_version_id,
        )

        if dry_run:
            session.rollback()
            logger.info("⚙️ Dry‑run complete — rolled back transactions")
        else:
            session.flush()
        return summary

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
            logger.warning(
                "⚠️ Event has no place: %s on %s", evt.get("event_type"), evt.get("date")
            )
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
        if not loc_out or loc_out.status == "unresolved" or not loc_out.normalized_name:
            status = getattr(loc_out, "status", "none") if loc_out else "none"
            logger.warning(
                "⚠️ Location not resolved: '%s' (status=%s, year=%s)",
                place,
                status,
                year,
            )
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
