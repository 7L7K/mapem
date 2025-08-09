import React, { useRef, useEffect, useState, useCallback } from "react";
import {
  MapContainer,
  TileLayer,
  useMap,
  ZoomControl,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import MapMarkers from "./MapMarkers";

// ─────────────────────────────────────────────────────────────────────────────

function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && Array.isArray(center)) {
      map.setView(center, map.getZoom());
      import.meta.env.DEV && console.log("🧭 [MigrationMap] Re-centering map to:", center);
    }
  }, [center, map]);
  return null;
}

export default function MigrationMap({
  movements = [],
  onMarkerClick = () => { },
  activePersonIds = new Set(),
}) {
  const mapRef = useRef(null);
  if (import.meta.env.DEV) console.log("🧠 [DEBUG] movements passed to MigrationMap:", movements);

  // ─── 1. Invalidate Leaflet size once on mount ────────────────────────────
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
        import.meta.env.DEV && console.log("🔁 [MigrationMap] invalidateSize()");
      }, 200);
    }
  }, []);

  // ─── 2. Build a map of locations that are missing lat/lng ────────────────
  const uniqueLocationsToGeocode = React.useMemo(() => {
    // Map location => array of movements using it
    const locMap = new Map();
    movements.forEach((mv) => {
      if (!mv.location) return;
      const key = String(mv.location).trim().toLowerCase();
      if (!locMap.has(key)) locMap.set(key, []);
      locMap.get(key).push(mv);
    });
    // Only include locations where at least one movement is missing lat/lng
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
  }, [movements]);

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
    return movements.map((mv) => {
      let [lat, lng] = [mv.latitude, mv.longitude];
      // If missing, try to use geocodedMap
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
  }, [movements, geocodedMap]);

  // filter movements with real coords
  const validMovements = finalMovements.filter(
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

  const dynamicCenter =
    validMovements.length > 0
      ? [validMovements[0]._markerLat, validMovements[0]._markerLng]
      : [37.8, -96];

  const resetView = useCallback(() => {
    if (!mapRef.current) return;
    mapRef.current.setView(dynamicCenter, 4);
  }, [dynamicCenter]);

  return (
    <div className="relative h-full w-full">
      <MapContainer
        key={`map-${validMovements.length}`}
        center={dynamicCenter}
        zoom={4}
        scrollWheelZoom
        zoomControl={false}
        style={{ height: "100%", width: "100%", background: "#101010" }}
        whenCreated={(m) => (mapRef.current = m)}
        tabIndex={0}
        aria-label="Migration map"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap contributors"
        />
        <ZoomControl position="bottomleft" />
        <RecenterMap center={dynamicCenter} />

        <MapMarkers movements={validMovements} onClick={onMarkerClick} />
      </MapContainer>

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

      {/* Reset View button */}
      <button
        onClick={resetView}
        className="absolute right-4 top-4 z-50 bg-black/70 text-white text-xs px-3 py-2 rounded-md border border-white/10 hover:bg-black/80"
        aria-label="Reset map view"
      >
        Reset View
      </button>
    </div>
  );
}
