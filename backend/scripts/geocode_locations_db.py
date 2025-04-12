#!/usr/bin/env python3
# File: scripts/geocode_locations_db.py

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Location
from backend.geocode import Geocode
from backend.config import DATABASE_URI

def main():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    geo = Geocode()

    to_geo = session.query(Location).filter(Location.latitude == None).all()
    print(f"🔍 Found {len(to_geo)} locations needing geocode")

    for loc in to_geo:
        lat, lon, norm, conf = geo.get_or_create_location(session, loc.name)
        if lat and lon:
            loc.latitude = lat
            loc.longitude = lon
            loc.normalized_name = norm
            loc.confidence_score = conf
            session.add(loc)
            print(f"✅ Geocoded '{loc.name}' → ({lat},{lon})")
        else:
            print(f"⚠️ Failed to geocode '{loc.name}'")

    session.commit()
    print("🎉 All done!")
    session.close()

if __name__ == "__main__":
    main()
