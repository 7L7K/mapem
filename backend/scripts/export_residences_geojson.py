import os
import psycopg2
import json
import logging
from psycopg2.extras import RealDictCursor
from backend import DB_CONFIG

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 'export_geojson.log')
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s - %(message)s')

print("🚀 Starting export_residences_geojson.py script...")

# Create data directory if it doesn't exist
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, 'residences.geojson')

def main():
    try:
        print("🧠 Connecting to DB with:", DB_CONFIG)
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query: Get events of type 'residence'
        # Join events with tree_people and locations
        query = """
        SELECT 
            e.id as event_id,
            e.event_type,
            e.date,
            tp.first_name,
            tp.last_name,
            l.place_name,
            l.latitude,
            l.longitude
        FROM events e
        LEFT JOIN tree_people tp ON e.person_id = tp.id
        LEFT JOIN locations l ON e.location_id = l.id
        WHERE e.event_type = 'residence';
        """
        print("📤 Running SQL query to fetch residence events...")
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"📌 Found {len(rows)} residence events.")
        logging.info(f"Found {len(rows)} residence events.")

        # Build GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for row in rows:
            # Check that coordinates exist and are valid
            if row['latitude'] is None or row['longitude'] is None:
                print(f"⚠️ Skipping event ID {row['event_id']} - missing coordinates.")
                logging.warning(f"Skipping event ID {row['event_id']} due to missing coordinates.")
                continue

            # Construct a feature with properties
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                },
                "properties": {
                    "event_id": row['event_id'],
                    "event_type": row['event_type'],
                    "date": row['date'],
                    "person": f"{row.get('first_name', '').strip()} {row.get('last_name', '').strip()}" or "Unknown",
                    "location": row['place_name']
                }
            }
            geojson["features"].append(feature)
            print(f"✅ Added event ID {row['event_id']} for {row['place_name']}")
            logging.info(f"Added event ID {row['event_id']} for {row['place_name']}")

        # Write the GeoJSON output
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"🎉 GeoJSON export completed successfully at {OUTPUT_FILE}")
        logging.info(f"GeoJSON export completed successfully. Output file: {OUTPUT_FILE}")

        conn.close()
    except Exception as e:
        logging.error(f"💥 ERROR: {str(e)}")
        print(f"💥 ERROR: {str(e)}")

if __name__ == "__main__":
    main()
