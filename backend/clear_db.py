# clear_db.py
from app.db import get_engine, SessionLocal
from sqlalchemy.sql import text
from app.models import Base  # Adjust import if your models live elsewhere

def clear_database():
    engine = get_engine()
    session = SessionLocal()
    try:
        # Using text() to safely execute raw SQL
        session.execute(text(
            "TRUNCATE TABLE individuals, families, events, locations, residence_history, tree_versions, tree_people, tree_relationships RESTART IDENTITY CASCADE"
        ))
        session.commit()
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error clearing database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_database()
