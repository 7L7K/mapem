# scripts/reset_db.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db import get_db
from backend.models import (
    Individual, Family, TreeRelationship, Event,
    Location, UploadedTree, TreeVersion
)

def nuke_everything():
    db = next(get_db())
    print("🔥 Deleting all data...")

    deletion_order = [
        TreeRelationship,
        Event,
        Individual,
        Family,
        Location,
        TreeVersion,        # 🔥 Move this BEFORE UploadedTree
        UploadedTree
    ]

    for model in deletion_order:
        count = db.query(model).delete()
        print(f"🧨 Deleted {count} from {model.__tablename__}")

    db.commit()
    db.close()
    print("✅ Database wiped clean.")

if __name__ == "__main__":
    nuke_everything()
