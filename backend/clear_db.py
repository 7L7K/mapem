# clear_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import models


def clear_database():
    # Connect to the database
    engine = create_engine('genealogy_db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Truncate all tables and reset auto-incrementing IDs
    try:
        session.execute('TRUNCATE TABLE individuals, families, events, locations, residence_history, tree_versions, tree_people, tree_relationships RESTART IDENTITY CASCADE')
        session.commit()
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error clearing database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_database()
