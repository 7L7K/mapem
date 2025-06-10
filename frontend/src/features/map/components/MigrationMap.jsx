// frontend/src/features/map/components/MigrationMap.jsx
import React, { useRef, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  ZoomControl,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// ─────────────────────────────────────────────────────────────────────────────
// Default Leaflet marker icon
// ─────────────────────────────────────────────────────────────────────────────
const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// ─────────────────────────────────────────────────────────────────────────────
// RecenterMap Component
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

// ─────────────────────────────────────────────────────────────────────────────
// MigrationMap
// ─────────────────────────────────────────────────────────────────────────────
export default function MigrationMap({
  movements = [],
  onMarkerClick = () => {},
  activePersonIds = new Set(),
}) {
  const mapRef = useRef(null);
  console.log("🧠 [DEBUG] movements passed to MigrationMap:", movements);


  // ─── 1. Invalidate Leaflet size once on mount ────────────────────────────
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
        import.meta.env.DEV && console.log("🔁 [MigrationMap] invalidateSize()");
      }, 200);
    }
  }, []);

  // ─── 2. Collect unique place strings ─────────────────────────────────────
  const uniqueLocations = React.useMemo(() => {
    const set = new Set();
    movements.forEach((mv) => {
      if (mv.location) set.add(String(mv.location).trim().toLowerCase());
    });
    return Array.from(set);
  }, [movements]);

  // ─── 3. geocodedMap state { place → [lat,lng]|null } ─────────────────────
  const [geocodedMap, setGeocodedMap] = useState({});

  // ─── 4. Fetch coords via backend /api/geocode?place=... ──────────────────
  useEffect(() => {
    if (uniqueLocations.length === 0) return;
    setGeocodedMap({});

    import.meta.env.DEV &&
      console.log("📍 [MigrationMap] Geocoding:", uniqueLocations);

    uniqueLocations.forEach(async (place) => {
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
  }, [uniqueLocations]);

  // ─── 5. Build finalMovements with fallback override ──────────────────────
  const finalMovements = React.useMemo(() => {
    return movements.map((mv) => {
      let [lat, lng] = [mv.latitude, mv.longitude];
      const fallback = lat === 37.8 && lng === -96;
      if (fallback && mv.location) {
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
    (mv) => typeof mv._markerLat === "number" && typeof mv._markerLng === "number",
  );

  // ─── 6. Dev warn for any still-null coords ───────────────────────────────
  useEffect(() => {
    if (!import.meta.env.DEV) return;
    const missing = finalMovements.filter(
      (mv) => typeof mv._markerLat !== "number" || typeof mv._markerLng !== "number",
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
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap contributors"
        />
        <ZoomControl position="bottomleft" />
        <RecenterMap center={dynamicCenter} />

        {validMovements.map((mv, idx) => (
          <Marker
            key={mv.event_id ?? idx}
            position={[mv._markerLat, mv._markerLng]}
            icon={defaultIcon}
            eventHandlers={{ click: () => onMarkerClick(mv.person_id) }}
          >
            <Popup>
              <strong>
                {Array.isArray(mv.names) && mv.names.length ? mv.names[0] : "Unknown"}
              </strong>
              <br />
              {mv.event_type} (
              {mv.date ? new Date(mv.date).getFullYear() || "?" : "?"})
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Dev HUD */}
      {import.meta.env.DEV && (
        <div className="absolute top-2 right-2 z-[9999] bg-black/70 text-white text-xs p-2 rounded shadow max-w-xs max-h-52 overflow-auto">
          <div>📝 movements fetched: {movements.length}</div>
          <div>📌 after fallback: {finalMovements.length}</div>
          <div>🗺️ displayed: {validMovements.length}</div>
          <div>🔍 unique geocodes: {uniqueLocations.length}</div>
          <div>
            🌍 resolved:{" "}
            {Object.values(geocodedMap).filter((v) => Array.isArray(v)).length} /{" "}
            {uniqueLocations.length}
          </div>
        </div>
      )}
    </div>
  );
}
