import os
import sys
from sqlalchemy.orm import sessionmaker
from backend.db import engine
from backend.models import Location
from backend.services.geocode import Geocode
from backend.utils.helpers import print_json

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
place = " ".join(sys.argv[1:])

if not place:
    print("❌ Provide a location string to geocode.")
    sys.exit(1)

Session = sessionmaker(bind=engine)
session = Session()

geocoder = Geocode(api_key=api_key)
result = geocoder.get_or_create_location(session, place)

# Double-check the result isn't None before subscripting
if not result:
    print("❌ Geocoding failed. No result returned.")
    sys.exit(1)

print_json(result)

normalized = result.get("normalized_name")
if not normalized:
    print("❌ Normalized name missing, can't save.")
    sys.exit(1)

loc = session.query(Location).filter_by(normalized_name=normalized).first()

if not loc:
    loc = Location(
        raw_name=result.get("raw_name"),
        name=result.get("name"),
        normalized_name=normalized,
        latitude=result.get("latitude"),
        longitude=result.get("longitude"),
        confidence_score=result.get("confidence_score"),
        confidence_label=result.get("confidence_label"),
        timestamp=result.get("timestamp"),
        source=result.get("source"),
        status=result.get("status"),
        historical_data=result.get("historical_data"),
    )
    session.add(loc)
    print(f"✅ Inserted new location into DB: {place}")
else:
    updated = False
    if not loc.confidence_label and result.get("confidence_label"):
        loc.confidence_label = result["confidence_label"]
        updated = True
    if result.get("confidence_score") is not None:
        loc.confidence_score = result["confidence_score"]
        updated = True
    if updated:
        print(f"🔄 Updated location entry: {place}")
    else:
        print(f"✅ No update needed for: {place}")

session.commit()
session.close()
