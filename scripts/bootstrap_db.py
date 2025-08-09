# scratch a quick script: scripts/bootstrap_db.py
from backend.models import Base
from backend.db import engine
from sqlalchemy import text

# This will CREATE TABLE for every Model defined under Base.metadata
with engine.begin() as conn:
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        print("🧩 postgis extension ensured")
    except Exception as e:
        print("⚠️ Could not enable PostGIS (ok on non-Postgres):", e)
Base.metadata.create_all(bind=engine)
print("✅ All tables created!")
