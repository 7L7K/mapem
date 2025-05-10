##/Users/kingal/mapem/backend/services/query_builders.py
"""
Build SQLAlchemy queries for the geo-timeline view.

Short-term goal  : be correct and reasonably fast.  
Long-term goal   : each filter lives in its own helper so we can unit-test
                   them in isolation.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Iterable, Set

from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Query, Session

from backend.models import Event, Location, Individual, Family
from backend.utils.debug import trace

logger = logging.getLogger("mapem")

# ── UI-label  → GEDCOM tag ──────────────────────────────────────────────
UI_TO_TAG = {
    "birth":     "birth",
    "death":     "death",
    "residence": "residence",
    "marriage":  "marriage",
    "burial":    "burial",
}

# ----------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------
def safe_in(col, values: Iterable) -> Any:
    """Return a `.in_()` clause that is always valid (even on empty sets)."""
    vals = list(values)
    return col.in_(vals) if vals else col == func.null()   # always FALSE


def _apply_event_type_filter(q: Query, filters: Dict[str, Any]) -> Query:
    raw_types = filters.get("eventTypes") or {}
    if not raw_types:
        logger.debug("🎛  No event type filters provided — skipping")
        return q

    active_ui_labels = [name.lower() for name, enabled in raw_types.items() if enabled]
    active_tags = [UI_TO_TAG.get(label, label.upper()) for label in active_ui_labels]

    logger.debug(f"🎛  UI event labels → {active_ui_labels}")
    logger.debug(f"📤 Translated GEDCOM tags → {active_tags}")

    if not active_tags:
        logger.warning("⚠️  Event type filter resulted in empty tag list — skipping")
        return q

    return q.filter(Event.event_type.in_(active_tags))


def _apply_year_filter(q: Query, filters: Dict[str, Any]) -> Query:
    yr0, yr1 = (filters.get("yearRange") or [None, None])[:2]
    logger.debug(f"📅 Year filter applied: from {yr0 or 'ANY'} to {yr1 or 'ANY'}")
    if yr0 is not None:
        q = q.filter(extract("year", Event.date) >= yr0)
    if yr1 is not None:
        q = q.filter(extract("year", Event.date) <= yr1)
    return q


def _apply_confidence_filter(q: Query, filters: Dict[str, Any]) -> Query:
    if filters.get("vague") in (True, "true", "1"):   # skip filter if vague
        return q
    logger.debug("🔍 Applying confidence filter: ≥ 0.6 only")
    return q.filter(
        Location.confidence_score.isnot(None),
        Location.confidence_score >= 0.6,
    )


def _expand_related_ids(
    session: Session,
    person_id: int,
    rel_filters: Dict[str, bool],
) -> Set[int]:
    """Return {person_id, …relatives…} depending on active relation toggles."""
    ids: Set[int] = {person_id}
    if not any(rel_filters.values()):
        return ids

    if rel_filters.get("siblings"):
        sib_q = (
            session.query(Individual.id)
            .join(
                Family,
                or_(
                    Family.husband_id == Individual.id,
                    Family.wife_id   == Individual.id,
                ),
            )
            .filter(
                or_(Family.husband_id == person_id, Family.wife_id == person_id)
            )
        )
        sibling_ids = {row.id for row in sib_q}
        logger.debug(f"🧑‍🤝‍🧑 Found {len(sibling_ids)} sibling IDs")
        ids |= sibling_ids

    # TODO: parents / cousins / spouses …
    return ids


def _apply_person_filter(
    session: Session, q: Query, filters: Dict[str, Any]
) -> Query:
    person_id = filters.get("selectedPersonId") or filters.get("person") or None
    if person_id is None:
        return q

    rel_filters = filters.get("relations") or {}
    logger.debug(f"👤 Person filter: selected={person_id}, relation filters={rel_filters}")
    person_ids = _expand_related_ids(session, person_id, rel_filters)
    logger.debug(f"👥 Resolved individual IDs: {sorted(person_ids)}")
    return q.filter(safe_in(Event.individual_id, person_ids))


def _apply_source_filter(q: Query, filters: Dict[str, Any]) -> Query:
    SOURCE_MAP = {
        "gedcom":  ["BIRT","DEAT","MARR","BURI","DIV"],
        "census":  ["census"],    # if you have an actual tag for census
        "manual":  ["manual"],    # likewise
        "ai":      ["ai"],
}
    chosen = [k for k, v in (filters.get("sources") or {}).items() if v]
    srcs = []
    for key in chosen:
        srcs.extend(SOURCE_MAP.get(key, []))
    if srcs:
        logger.debug(f"🔗 source tags filter → {srcs}")
        q = q.filter(Event.source_tag.in_(srcs))
    return q


# ----------------------------------------------------------------------
# public builder
# ----------------------------------------------------------------------
@trace("build_event_query")
def build_event_query(
    session: Session, tree_version_id: int, filters: Dict[str, Any]
) -> Query:
    """
    Build the filtered Event query.  **DO NOT** call .all() / .count() here;
    the caller decides what to do with the query object.
    """
    # 🚀 Top-level entry
    logger.debug("⚙️  build_event_query() start")
    logger.debug(f"  • tree_version_id = {tree_version_id}")
    logger.debug(f"  • raw filters = {filters!r}")

    q = (
        session.query(Event)
        .join(Location, Event.location_id == Location.id)
        .filter(Event.tree_version_id == tree_version_id)
    )

    # —— apply filters in cheap-to-expensive order ——
    q = _apply_event_type_filter(q, filters)
    logger.debug("  → after event_type_filter: SQL so far:\n%s",
                 q.statement.compile(compile_kwargs={"literal_binds": True}))

    q = _apply_year_filter(q, filters)
    logger.debug("  → after year_filter: SQL so far:\n%s",
                 q.statement.compile(compile_kwargs={"literal_binds": True}))

    q = _apply_confidence_filter(q, filters)
    logger.debug("  → after confidence_filter: SQL so far:\n%s",
                 q.statement.compile(compile_kwargs={"literal_binds": True}))

    q = _apply_source_filter(q, filters)
    logger.debug("  → after source_filter: SQL so far:\n%s",
                 q.statement.compile(compile_kwargs={"literal_binds": True}))

    q = _apply_person_filter(session, q, filters)
    logger.debug("  → after person_filter: SQL so far:\n%s",
                 q.statement.compile(compile_kwargs={"literal_binds": True}))

    # —— last: emit SQL for dev eyes only ——
    if logger.isEnabledFor(logging.DEBUG):
        try:
            compiled = q.statement.compile(compile_kwargs={"literal_binds": True})
            sql_text = str(compiled)
            logger.debug("🧾 final SQL ↓")
            logger.debug(sql_text)

            # Save last query for deep dive

            # Save last query for deep dive
            with open("/tmp/mapem_last_query.sql", "w") as f:
                f.write(sql_text)
        except Exception as exc:
            logger.warning("⚠️ could not compile SQL: %s", exc)
    logger.debug("⚙️  build_event_query() end")
    return q
