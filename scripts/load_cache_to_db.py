#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read geocode_cache.json and upsert into the DB: 
  - INSERT brand-new normalized_name’s
  - UPDATE lat/lng on any existing normalized_name that still has NULL coords
  - LOG ALL DECISIONS (inserted / updated / skipped) with reason
"""

import json, os
from datetime import datetime
from backend.db import SessionLocal
from backend.models import Location

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "geocode_cache.json")

def main():
    print(f"📂 Reading cache from {CACHE_FILE}")
    cache = json.load(open(CACHE_FILE, "r"))
    session = SessionLocal()

    inserted = 0
    updated  = 0
    skipped  = 0

    for raw_key, entry in cache.items():
        try:
            lat, lng, norm_name, score = entry
        except Exception as e:
            print(f"❌ Failed to unpack cache entry {raw_key}: {entry} — {e}")
            continue

        print(f"\n🌍 Processing → raw_key: {raw_key} | normalized_name: {norm_name}")

        loc = (
            session.query(Location)
            .filter(Location.normalized_name.ilike(norm_name))
            .one_or_none()
        )

        if not loc:
            print(f"🔍 Not found by normalized_name → trying raw_name fallback...")
            loc = (
                session.query(Location)
                .filter(Location.raw_name.ilike(norm_name))
                .one_or_none()
            )

        if loc:
            print(f"✅ Found existing row → ID: {loc.id}")
            if loc.latitude is None or loc.longitude is None:
                print(f"✏️ Updating NULL coords → lat: {lat}, lng: {lng}")
                loc.latitude         = lat
                loc.longitude        = lng
                loc.confidence_score = score
                loc.updated_at       = datetime.utcnow()
                updated += 1
            else:
                print(f"🚫 Skipping — coords already set (lat: {loc.latitude}, lng: {loc.longitude})")
                skipped += 1
        else:
            print(f"➕ Inserting new location for: {norm_name}")
            new_loc = Location(
                raw_name         = norm_name,
                normalized_name  = norm_name,
                latitude         = lat,
                longitude        = lng,
                confidence_score = score,
                source           = "cache",
                status           = "ok",
                created_at       = datetime.utcnow(),
                updated_at       = datetime.utcnow(),
            )
            session.add(new_loc)
            inserted += 1

    session.commit()
    session.close()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ inserted: {inserted}")
    print(f"✏️  updated: {updated}")
    print(f"🚫 skipped: {skipped}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    main()
