# clear_db.py
from sqlalchemy.sql import text
from backend.db import get_engine, SessionLocal
from backend.models import Base
from backend.db import get_db

def clear_database():
    engine = get_engine()
    db = next(get_db())
    try:
        # Using text() to safely execute raw SQL
        db.execute(text(
            "TRUNCATE TABLE individuals, families, events, locations, residence_history, tree_versions, tree_people, tree_relationships RESTART IDENTITY CASCADE"
        ))
        db.commit()
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_database()
