#!/usr/bin/env python

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.utils import get_db_connection
from backend.models import Location

def print_all_locations():
    session = get_db_connection()
    all_locations = session.query(Location).order_by(Location.name).all()
    
    print("📍 All Locations in DB:\n")

    for loc in all_locations:
        lat = f"{loc.latitude:.5f}" if loc.latitude else "None"
        lng = f"{loc.longitude:.5f}" if loc.longitude else "None"
        status = "✅ Geocoded" if loc.latitude and loc.longitude else "❌ Missing"
        print(f"- {loc.name} → normalized: [{loc.normalized_name}] | lat: {lat} | lng: {lng} | {status}")

    session.close()

if __name__ == "__main__":
    print_all_locations()
