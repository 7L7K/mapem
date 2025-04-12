# backend/scripts/fix_missing_coords.py

import os
import sys
from datetime import datetime

# 🔧 Set up path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.db_utils import get_db_connection
from backend.geocode import Geocode
from backend.models import Location

session = get_db_connection()
geocoder = Geocode()

# 🌍 Find all locations with no lat/lng
missing_coords = session.query(Location).filter(
    (Location.latitude == None) | (Location.longitude == None)
).all()

print(f"📊 Found {len(missing_coords)} locations with missing coordinates")

for loc in missing_coords:
    place = loc.name
    norm = loc.normalized_name
    print(f"\n🔍 Trying: {place} ({norm})")

    # Try to get from the standard cached geocoder
    lat, lng, norm_new, conf = geocoder.get_or_create_location(session, place)

    if lat and lng:
        print(f"✅ Got coordinates for {place}: ({lat}, {lng})")

        # Only update if coordinates were previously missing
        if not loc.latitude or not loc.longitude:
            print(f"🛠️ Updating DB for {norm}")
            loc.latitude = lat
            loc.longitude = lng
            loc.confidence_score = conf or 0.9
            loc.timestamp = datetime.utcnow()
            session.commit()
    else:
        print(f"❌ No result from cached geocoder — forcing API retry...")
        
        # Try a fresh lookup that ignores cache
        lat, lng, norm_fresh, conf_fresh = geocoder.force_geocode(place)

        if lat and lng:
            print(f"🚀 Fresh API worked! Updating DB for {place}")
            loc.latitude = lat
            loc.longitude = lng
            loc.confidence_score = conf_fresh or 0.8
            loc.timestamp = datetime.utcnow()
            session.commit()
        else:
            print(f"💤 Still no luck with {place}")
