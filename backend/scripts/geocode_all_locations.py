#!/usr/bin/env python
import os
import json
import csv
import argparse
from backend.utils import get_db_connection, normalize_location_name, calculate_name_similarity
from backend.models import Location
from backend.geocode import Geocode

def geocode_all_locations(export_csv=False, csv_filename="geocoded_locations.csv"):
    # Open a DB connection
    session = get_db_connection()
    geocoder = Geocode()  # Use default API fallback (Google if key provided, else Nominatim)

    # Get all location records from DB
    all_locations = session.query(Location).all()
    results = {"geocoded": [], "missing": []}

    for loc in all_locations:
        # Check if location is already geocoded (using the column names from models: latitude & longitude)
        if loc.latitude is not None and loc.longitude is not None:
            results["geocoded"].append({
                "raw": loc.name,
                "normalized": loc.normalized_name,
                "lat": float(loc.latitude),
                "lng": float(loc.longitude),
                "confidence": loc.confidence_score,
            })
        else:
            # If missing, run the geocoder
            lat, lng, norm_name, conf = geocoder.get_or_create_location(session, loc.name)
            if lat is not None and lng is not None:
                # Update DB record with geocode info
                loc.latitude = lat
                loc.longitude = lng
                loc.normalized_name = norm_name
                loc.confidence_score = conf
                session.add(loc)
                results["geocoded"].append({
                    "raw": loc.name,
                    "normalized": norm_name,
                    "lat": float(lat),
                    "lng": float(lng),
                    "confidence": conf,
                })
            else:
                results["missing"].append(loc.name)
    
    # Commit changes and close session
    session.commit()
    session.close()
    
    # Print the summary in the console
    print("✅ Geocoded Locations:")
    for loc in results["geocoded"]:
        print(f"- {loc['normalized']} ({loc['lat']}, {loc['lng']}) - Confidence: {loc['confidence']}")
    
    if results["missing"]:
        print("\n❌ Still Missing Geocode:")
        for raw in results["missing"]:
            print(f"- {raw}")
    else:
        print("\nAll locations successfully geocoded!")
        
    # Optional CSV export if the flag is provided
    if export_csv:
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["raw", "normalized", "lat", "lng", "confidence"])
            writer.writeheader()
            for loc in results["geocoded"]:
                writer.writerow(loc)
        print(f"\nCSV exported to: {csv_filename}")

def main():
    parser = argparse.ArgumentParser(
        description="Geocode all locations in the DB and optionally export results to CSV."
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export geocoded locations to a CSV file."
    )
    parser.add_argument(
        "--csv-filename",
        type=str,
        default="geocoded_locations.csv",
        help="Filename for CSV export (default: geocoded_locations.csv)."
    )
    args = parser.parse_args()

    geocode_all_locations(export_csv=args.export_csv, csv_filename=args.csv_filename)

if __name__ == "__main__":
    main()
