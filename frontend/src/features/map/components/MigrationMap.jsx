import React, { useEffect, useState } from "react";
import DeckMigrationMap from "./DeckMigrationMap";
import MapWarnings from "@shared/components/MapHUD/MapWarnings";

// ─────────────────────────────────────────────────────────────────────────────

// Deck version does its own view management

export default function MigrationMap({
  movements = [],
  onMarkerClick = () => { },
  activePersonIds = new Set(),
  year,
  onSelect,
}) {
  if (import.meta.env.DEV) console.log("🧠 [DEBUG] movements passed to MigrationMap:", movements);

  const isSegments = Array.isArray(movements) && movements.length > 0 && movements[0] && movements[0].from && movements[0].to;

  // ─── 2. Build a map of locations that are missing lat/lng (only for pin mode) ────────────────
  const uniqueLocationsToGeocode = React.useMemo(() => {
    if (isSegments) return [];
    const locMap = new Map();
    movements.forEach((mv) => {
      if (!mv.location) return;
      const key = String(mv.location).trim().toLowerCase();
      if (!locMap.has(key)) locMap.set(key, []);
      locMap.get(key).push(mv);
    });
    return Array.from(locMap.entries())
      .filter(([loc, mvs]) =>
        mvs.some(
          (mv) =>
            mv.latitude === undefined ||
            mv.longitude === undefined ||
            mv.latitude === null ||
            mv.longitude === null ||
            isNaN(Number(mv.latitude)) ||
            isNaN(Number(mv.longitude))
        )
      )
      .map(([loc]) => loc);
  }, [movements, isSegments]);

  // ─── 3. geocodedMap state { place → [lat,lng]|null } ─────────────────────
  const [geocodedMap, setGeocodedMap] = useState({});

  // ─── 4. Fetch coords via backend /api/geocode?place=... ──────────────────
  useEffect(() => {
    if (uniqueLocationsToGeocode.length === 0) return;
    setGeocodedMap({});

    import.meta.env.DEV &&
      console.log("📍 [MigrationMap] Geocoding ONLY unresolved:", uniqueLocationsToGeocode);

    uniqueLocationsToGeocode.forEach(async (place) => {
      if (!place || place.length > 150) {
        import.meta.env.DEV && console.warn(`[Geocode 🧹] Skipping invalid place: "${place}"`);
        setGeocodedMap((prev) => ({ ...prev, [place]: null }));
        return;
      }

      try {
        const res = await fetch(`/api/geocode?place=${encodeURIComponent(place)}`);
        if (!res.ok) {
          const text = await res.text();
          import.meta.env.DEV &&
            console.error(`[Geocode ❌] ${res.status} ${res.statusText} – "${place}"`, text);
          setGeocodedMap((prev) => ({ ...prev, [place]: null }));
          return;
        }

        const data = await res.json();
        const { latitude, longitude } = data;

        if (latitude !== undefined && longitude !== undefined) {
          setGeocodedMap((prev) => ({ ...prev, [place]: [latitude, longitude] }));
          import.meta.env.DEV &&
            console.log(`✅ [Geocode] "${place}" → [${latitude}, ${longitude}]`);
        } else {
          setGeocodedMap((prev) => ({ ...prev, [place]: null }));
          import.meta.env.DEV && console.warn(`⚠️ [Geocode] Unresolved "${place}"`, data);
        }
      } catch (err) {
        setGeocodedMap((prev) => ({ ...prev, [place]: null }));
        import.meta.env.DEV &&
          console.error(`❌ [Geocode ERROR] "${place}" –`, err.message || err);
      }
    });
  }, [uniqueLocationsToGeocode]);

  // ─── 5. Build finalMovements with fallback override ──────────────────────
  const finalMovements = React.useMemo(() => {
    if (isSegments) return movements;
    return movements.map((mv) => {
      let [lat, lng] = [mv.latitude, mv.longitude];
      if (
        (lat === undefined || lng === undefined || lat === null || lng === null || isNaN(Number(lat)) || isNaN(Number(lng))) &&
        mv.location
      ) {
        const key = String(mv.location).trim().toLowerCase();
        if (Array.isArray(geocodedMap[key])) {
          [lat, lng] = geocodedMap[key];
        }
      }
      return { ...mv, _markerLat: lat, _markerLng: lng };
    });
  }, [movements, geocodedMap, isSegments]);

  // filter movements with real coords
  const validMovements = isSegments
    ? []
    : finalMovements.filter(
      (mv) => typeof mv._markerLat === "number" && typeof mv._markerLng === "number" && !isNaN(mv._markerLat) && !isNaN(mv._markerLng),
    );

  // ─── 6. Dev warn for any still-null coords ───────────────────────────────
  useEffect(() => {
    if (!import.meta.env.DEV) return;
    const missing = finalMovements.filter(
      (mv) => typeof mv._markerLat !== "number" || typeof mv._markerLng !== "number" || isNaN(mv._markerLat) || isNaN(mv._markerLng)
    );
    if (missing.length) {
      console.warn("⚠️ [MigrationMap] Missing coords:", missing);
    } else {
      console.log("✅ [MigrationMap] All movements resolved:", validMovements.length);
    }
  }, [finalMovements, validMovements.length]);

  const dynamicCenter = (() => {
    if (isSegments && movements.length > 0 && movements[0].from) {
      return [Number(movements[0].from.lat) || 37.8, Number(movements[0].from.lng) || -96];
    }
    if (validMovements.length > 0) {
      return [validMovements[0]._markerLat, validMovements[0]._markerLng];
    }
    return [37.8, -96];
  })();

  return (
    <div className="relative h-full w-full">
      <DeckMigrationMap
        movements={validMovements}
        year={year}
        onSelect={(sel) => {
          if (sel?.type === "point" && sel.data?.person_id) {
            onMarkerClick(sel.data.person_id);
          }
          if (typeof onSelect === 'function') onSelect(sel)
        }}
      />

      {/* Dev HUD */}
      {import.meta.env.DEV && (
        <div className="absolute top-2 right-2 z-[9999] bg-black/70 text-white text-xs p-2 rounded shadow max-w-xs max-h-52 overflow-auto">
          <div>📝 movements fetched: {movements.length}</div>
          <div>📌 after fallback: {finalMovements.length}</div>
          <div>🗺️ displayed: {validMovements.length}</div>
          <div>🔍 unique geocodes needed: {uniqueLocationsToGeocode.length}</div>
          <div>
            🌍 resolved:{" "}
            {Object.values(geocodedMap).filter((v) => Array.isArray(v)).length} /{" "}
            {uniqueLocationsToGeocode.length}
          </div>
        </div>
      )}

      {/* QA warnings for segments */}
      {isSegments && <MapWarnings segments={movements} />}

    </div>
  );
}
