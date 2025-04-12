# backend/scripts/test_geocode.py

import os
import sys

# 🔧 Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.geocode import Geocode  
from backend.db_utils import get_db_connection
from backend.models import Location

session = get_db_connection()
geocoder = Geocode()

places = ["Detroit, Michigan, USA"]

for place in places:
    lat, lng, norm, conf = geocoder.get_or_create_location(session, place)
    print(f"📍 {place} → {lat}, {lng}, conf={conf}")
    print(f"🧠 Trying to update normalized_name = {norm}")

    # 🔍 Try exact normalized name match first
    existing = session.query(Location).filter_by(normalized_name=norm).first()

    # 🪃 Fallback to loose match using original name
    if not existing:
        print(f"🪃 Fallback: searching for locations where name ILIKE '%{place}%'")
        existing = session.query(Location).filter(Location.name.ilike(f"%{place}%")).first()

    # 🔧 Update if match found and coords missing
    if existing and (not existing.latitude or not existing.longitude):
        print(f"🛠️ Updating: {existing.name}")
        existing.latitude = lat
        existing.longitude = lng
        existing.confidence_score = conf
        session.commit()
        print(f"✅ Coordinates updated in DB for {existing.normalized_name}")
    elif existing:
        print(f"✅ Already exists with coords: {existing.normalized_name}")
    else:
        print(f"❌ No matching location found to update: {place}")
