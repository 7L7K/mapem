import logging
from typing import Any, Dict, Iterable, Set, List

from sqlalchemy import extract, func, or_, select
from sqlalchemy.orm import Query, Session

from backend.models import Event, Location, Individual, Family
from backend.models.event import event_participants      # ⬅️ NEW
from backend.db import SessionLocal

logger = logging.getLogger("mapem.query_builders")

# ─── UI tag → DB tag map ───────────────────────────────────────
UI_TO_TAG = {
    "birth":     "birth",
    "death":     "death",
    "residence": "residence",
    "marriage":  "marriage",
    "burial":    "burial",
}

# ─── Helpers ──────────────────────────────────────────────────
def _normalize_event_type_input(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [UI_TO_TAG.get(t.lower(), t.lower()) for t in raw]
    if isinstance(raw, dict):
        return [UI_TO_TAG.get(k.lower(), k.lower()) for k, v in raw.items() if v]
    logger.warning("⚠️ Unsupported eventTypes payload: %r", raw)
    return []

def safe_in(col, values: Iterable):
    vals = list(values)
    logger.debug("safe_in values=%s", vals)
    return col.in_(vals) if vals else col == func.null()

# ─── Filter applicators ───────────────────────────────────────
def _apply_event_type_filter(q: Query, filters: Dict[str, Any]) -> Query:
    tags = _normalize_event_type_input(filters.get("eventTypes"))
    logger.debug("_apply_event_type_filter tags=%s", tags)
    if not tags:
        logger.debug("⚠️ Empty eventTypes — skipping filter.")
        return q
    return q.filter(Event.event_type.in_(tags))

def _apply_year_filter(q: Query, filters: Dict[str, Any]) -> Query:
    yr = filters.get("year", {})
    yr0, yr1 = yr.get("min"), yr.get("max")
    logger.debug("_apply_year_filter %s-%s", yr0, yr1)
    if yr0 is not None:
        q = q.filter(extract("year", Event.date) >= yr0)
    if yr1 is not None:
        q = q.filter(extract("year", Event.date) <= yr1)
    return q

def _apply_confidence_filter(q: Query, filters: Dict[str, Any]) -> Query:
    if filters.get("vague"):
        logger.debug("vague=True → skipping confidence filter")
        return q

    try:
        thresh = float(filters.get("confidenceThreshold", 0.6))
    except (TypeError, ValueError):
        thresh = 0.6
    logger.debug("_apply_confidence_filter thresh=%s", thresh)

    if thresh <= 0:
        return q

    return q.filter(
        or_(Location.confidence_score.is_(None),
            Location.confidence_score >= thresh)
    )

def _expand_related_ids(session: Session, pid: int, rels: Dict[str, bool]) -> Set[int]:
    ids = {pid}
    if rels.get("siblings"):
        sibs = {
            r.id
            for r in session.query(Individual.id)
                            .join(Family)
                            .filter(or_(Family.husband_id == pid,
                                        Family.wife_id == pid))
        }
        logger.debug("siblings=%s", sibs)
        ids |= sibs
    # add more relations later
    return ids

# ─── Source tag filter ────────────────────────────────────────
GEDCOM_TAGS = {"BIRT", "DEAT", "RESI", "MARR", "BURI"}

def _apply_source_filter(q: Query, filters: Dict[str, Any]) -> Query:
    raw = filters.get("sources") or []
    srcs = (
        [s.lower() for s in raw] if isinstance(raw, list)
        else [k.lower() for k, v in raw.items() if v] if isinstance(raw, dict)
        else []
    )

    expanded = {"gedcom" if tag == "gedcom" else tag for tag in srcs}

    if not expanded:
        logger.debug("_apply_source_filter → none supplied")
        return q

    logger.debug("_apply_source_filter srcs=%s", expanded)
    return q.filter(Event.source_tag.in_(expanded))

def _apply_person_filter(session: Session, q: Query, filters: Dict[str, Any]) -> Query:
    pid_raw = filters.get("person")
    if not pid_raw:
        return q
    try:
        pid = int(pid_raw)
    except (ValueError, TypeError):
        logger.warning("⚠️ Invalid person id %r — skipping", pid_raw)
        return q

    ids = _expand_related_ids(session, pid, filters.get("relations", {}))
    if not ids:
        return q

    q = q.join(Event.participants)
    q = q.filter(Individual.id.in_(ids))
    return q

# ─── Main query builder & visible counts ──────────────────────
def build_event_query(session: Session, tree_id: int, filters: Dict[str, Any]) -> Query:
    logger.debug("⚙️ build_event_query tree_id=%s filters=%s", tree_id, filters)
    q = (session.query(Event)
         .outerjoin(Location)
         .filter(Event.tree_id == tree_id))

    q = _apply_event_type_filter(q, filters)
    q = _apply_year_filter(q,          filters)
    q = _apply_confidence_filter(q,    filters)
    q = _apply_source_filter(q,        filters)
    q = _apply_person_filter(session,  q, filters)

    try:
        logger.debug("🧾 final SQL:\n%s",
                     q.statement.compile(compile_kwargs={"literal_binds": True}))
    except Exception as e:
        logger.warning("⚠️ SQL compile failed: %s", e)

    return q

def compute_visible_counts(tree_id: int, filters: Dict[str, Any]) -> Dict[str, int]:
    logger.debug("🧮 compute_visible_counts tree=%s", tree_id)
    session = SessionLocal()
    try:
        q = build_event_query(session, tree_id, filters)
        rows = (q.with_entities(Event.event_type, func.count().label("cnt"))
                  .group_by(Event.event_type)
                  .all())
        return {row.event_type: row.cnt for row in rows}
    except Exception:
        logger.exception("💥 compute_visible_counts crashed")
        return {}
    finally:
        session.close()
