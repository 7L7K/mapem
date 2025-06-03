# scratch a quick script: scripts/bootstrap_db.py
from backend.models import Base
from backend.db import engine

# This will CREATE TABLE for every Model defined under Base.metadata
Base.metadata.create_all(bind=engine)
print("✅ All tables created!")
