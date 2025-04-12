# backend/scripts/reset_database.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.models import Base
from backend.db import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect

print("⚠️ WARNING: This will DELETE everything in your database.")

Session = sessionmaker(bind=engine)
session = Session()

try:
    # Drop all tables
    print("🔨 Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    # Recreate schema
    print("🧱 Rebuilding all tables...")
    Base.metadata.create_all(bind=engine)

    # Verify it's empty
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in tables:
        result = session.execute(f"SELECT COUNT(*) FROM {table};")
        count = result.scalar()
        print(f"✅ {table}: {count} rows")

    print("✅ Database reset complete!")

except Exception as e:
    print("🔥 Error during reset:", str(e))
    import traceback
    print(traceback.format_exc())

finally:
    session.close()
