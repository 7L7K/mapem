# geocode_missing_locations.py

import os
import sys
import time

# 🔧 Add your project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print(f"📁 PYTHONPATH set to include: {PROJECT_ROOT}")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geocode import Geocode
from models import Location
from utils import normalize_location_name

# Set this if you're using Google Maps API
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Setup SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://kingal@localhost/genealogy_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def geocode_missing():
    session = Session()
    geocoder = Geocode(api_key=GOOGLE_API_KEY)

    missing = (
        session.query(Location)
        .filter((Location.latitude == None) | (Location.longitude == None))
        .all()
    )

    print(f"📍 {len(missing)} locations missing coordinates")

    for loc in missing:
        print(f"\n🌐 Geocoding: {loc.name or loc.normalized_name} (ID: {loc.id})")
        lat, lng, norm_name, conf = geocoder.force_geocode(loc.name or loc.normalized_name)

        if lat is not None and lng is not None:
            loc.latitude = lat
            loc.longitude = lng
            loc.normalized_name = norm_name or normalize_location_name(loc.name)
            loc.confidence_score = conf
            loc.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ Updated: ({lat}, {lng}) | Confidence: {conf}")
        else:
            print("❌ Skipped – no result")

        time.sleep(1)  # Avoid rate limiting on Nominatim

    session.commit()
    session.close()
    print("🎉 Done updating missing locations.")

if __name__ == "__main__":
    geocode_missing()




