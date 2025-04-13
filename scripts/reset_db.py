#!/usr/bin/env python
from backend import config, models  # Adjust import paths as needed
from backend.db import get_engine

# Create the engine using your configuration
engine = get_engine()

def reset_database():
    print("Dropping all tables...")
    models.Base.metadata.drop_all(engine)
    print("Creating all tables...")
    models.Base.metadata.create_all(engine)
    print("Database reset complete.")

if __name__ == '__main__':
    reset_database()
