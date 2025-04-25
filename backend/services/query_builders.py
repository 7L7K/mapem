# backend/services/query_builders.py
from sqlalchemy import func, or_
from backend.models import Event, Location, Individual, Family

def build_event_query(session, tree_id, filters):
    """
    Returns a SQLAlchemy query of Event rows filtered by the provided dict.
    """
    q = (session.query(Event)
              .join(Location, Event.location_id == Location.id)
              .filter(Event.tree_id == tree_id))

    # ── Event types (birth / death / residence …)
    active_types = [k for k, v in (filters.get("eventTypes") or {}).items() if v]
    if active_types:
        q = q.filter(Event.event_type.in_(active_types))

    # ── Year range
    yr_min, yr_max = filters.get("yearRange", [None, None])
    if yr_min is not None and yr_max is not None:
        q = q.filter(func.extract("year", Event.date)
                       .between(int(yr_min), int(yr_max)))

    # ── Source filter  (GEDCOM / census / manual / ai)
    active_sources = [k for k, v in (filters.get("sources") or {}).items() if v]
    if active_sources:
        q = q.filter(Event.source_tag.in_(active_sources))

    # ── Vague toggle
    if filters.get("vague") is False:
        q = q.filter(Location.status != "vague")

    # ── Person + relations
    pid = filters.get("selectedPersonId")
    if pid:
        # always include the focal person
        person_ids = {pid}

        rel_types = [k for k, v in (filters.get("relations") or {}).items() if v]
        if rel_types and rel_types != ["self"]:
            # quick + dirty: use Event relationships for now
            # (better: a pre-computed relatives table)
            rel_q = (session.query(Individual.id)
                            .join(Family, or_(Family.husband_id == Individual.id,
                                              Family.wife_id == Individual.id))
                            .filter(Individual.tree_id == tree_id))
            if "siblings" in rel_types:
                rel_q = rel_q.filter(
                    or_(Family.husband_id == pid, Family.wife_id == pid)
                )
            # expand with parents / cousins logic later …
            person_ids |= {row.id for row in rel_q}

        q = q.filter(Event.individual_id.in_(person_ids))
    print("🧠 Final SQL query:", str(q.statement.compile(compile_kwargs={"literal_binds": True})))


    return q
