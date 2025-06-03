from sqlalchemy.orm import sessionmaker
from backend.db import get_engine
from backend.models.location import Location
from backend.tasks.geocode_tasks import geocode_location_task
from sqlalchemy import not_


# Init session
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
resolved_statuses = [
    "valid",
    "vague_state",
    "historical",
    "manual_override",
    "ok",
]

def main():
    unresolved = (
        session.query(Location.id)
        .filter(Location.latitude.is_(None))
        .filter(not_(Location.status.in_(resolved_statuses)))
        .all()
)


    print(f"📦 Queuing {len(unresolved)} unresolved locations...")

    for (loc_id,) in unresolved:
        print(f"➡️ Queuing ID {loc_id}")
        geocode_location_task.delay(loc_id)

    print("✅ Done queuing.")

if __name__ == "__main__":
    main()
