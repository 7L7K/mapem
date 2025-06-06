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
// RecenterMap Component: Whenever `center` changes, call map.setView(...)  
// ─────────────────────────────────────────────────────────────────────────────
function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && Array.isArray(center)) {
      map.setView(center, map.getZoom());
      if (import.meta.env.DEV) {
        console.log("🧭 [MigrationMap] Re-centering map to:", center);
      }
    }
  }, [center, map]);
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// MigrationMap Main Component
//
// Props:
//
//  - movements: array of movement objects from your API.  
//      Each object has at least these keys (per your sample):
//        • latitude: 37.8          (number, often fallback)
//        • longitude: -96         (number, often fallback)
//        • location: "mississippi" (string—the place name to geocode)
//        • names: ["William Mckinley"] (array of person‐names; pick index 0)
//        • event_type: "birth"    (string)
//        • date: "1888-04-24"     (string)
//        • person_id: 1288        (number or null)
//        • event_id: 1675         (number)
//        • …and other fields like confidence_label, etc.
//
//  - onMarkerClick:   function(person_id) => void
//  - activePersonIds: Set of person_id(s) you want to highlight
//
// This version will:
//
//   1. Render **all** movements, even if lat/lng are the fallback `[37.8, -96]`.
//   2. Look at each movement’s `mv.location` string, collect every unique name.
//   3. Fire off a Nominatim lookup for that place name once (on mount or whenever the list changes).
//   4. Store each successful geocode in a `geocodedMap` – e.g. { "mississippi": [31.0, -89.0], … }.
//   5. When rendering, if `mv.latitude === 37.8 && mv.longitude === -96`, replace it with the real geocode.
//   6. If the geocode lookup fails (no result), we’ll keep the fallback `[37.8, -96]` so you at least see something.
//
// After dropping this file in, restart your dev server and check the console. You’ll see logs like:
//
//    • “Unique locations to geocode: ['mississippi', 'arkansas', …]”  
//    • “Geocoded ‘mississippi’ → [31.00096, -89.66453]”  
//    • “Failed to geocode ‘some‐place’”  (if that ever happens)  
//    • Then each marker’s final lat/lng and popup info.
//
// Once real geocodes are in place, your map pins will spread out instead of clustering at [37.8, –96].
export default function MigrationMap({
  movements = [],
  onMarkerClick = () => {},
  activePersonIds = new Set(),
}) {
  const mapRef = useRef(null);

  // ───────────────────────────────────────────────────────────────────────────
  // 1. Invalidate size once on mount, so Leaflet renders properly:
  // ───────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
        if (import.meta.env.DEV) {
          console.log("🔁 [MigrationMap] Forcing map redraw (invalidateSize)");
        }
      }, 200);
    }
  }, []);

  // ───────────────────────────────────────────────────────────────────────────
  // 2. Build a list of all unique `location` strings from movements
  //    (we’ll geocode each only once, then cache).
  // ───────────────────────────────────────────────────────────────────────────
  const uniqueLocations = React.useMemo(() => {
    const set = new Set();
    for (const mv of movements) {
      if (typeof mv.location === "string" && mv.location.trim().length > 0) {
        set.add(mv.location.trim().toLowerCase());
      }
    }
    return Array.from(set);
  }, [movements]);

  // ───────────────────────────────────────────────────────────────────────────
  // 3. geocodedMap: { [locationName]: [lat, lng] }  
  //    missing or failed entries remain undefined.
  // ───────────────────────────────────────────────────────────────────────────
  const [geocodedMap, setGeocodedMap] = useState({});

  // ───────────────────────────────────────────────────────────────────────────
  // 4. Whenever `uniqueLocations` changes, fire off Nominatim lookups.
  //
  // For each locationName, do a GET to `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURI(locationName)}`.
  // If we get a non‐empty array back, pick the first element’s `lat`/`lon` and store it.
  // If it fails (no results, network error), we skip that name (fallback still `[37.8, -96]`).
  // ───────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (uniqueLocations.length === 0) return;

    // Start with a fresh map (so we can show logs of success/fail freshly)
    setGeocodedMap({});

    if (import.meta.env.DEV) {
      console.log("📍 [MigrationMap] Unique locations to geocode:", uniqueLocations);
    }

    uniqueLocations.forEach((locName) => {
      // Nominatim requires a custom User‐Agent or “Referer” header.
      // In the browser, fetch will automatically set a reasonable Referer.
      // We’ll just call the endpoint directly.
      //
      // NOTE: If your project has a backend geocode endpoint (using your GEOCODE_API_KEY),
      // you can replace this fetch URL with your own `/api/geocode?place=${encodeURIComponent(locName)}`.
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locName)}`;

      fetch(url, {
        method: "GET",
        headers: {
          "Accept-Language": "en", // optional: limit to English results
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data) && data.length > 0) {
            const first = data[0];
            const lat = parseFloat(first.lat);
            const lng = parseFloat(first.lon);
            if (!isNaN(lat) && !isNaN(lng)) {
              setGeocodedMap((prev) => ({
                ...prev,
                [locName]: [lat, lng],
              }));
              if (import.meta.env.DEV) {
                console.log(`✅ [Geocode] “${locName}” → [${lat}, ${lng}]`);
              }
              return;
            }
          }
          // If no result or invalid, mark as failed
          setGeocodedMap((prev) => ({
            ...prev,
            [locName]: null,
          }));
          if (import.meta.env.DEV) {
            console.warn(`⚠️ [Geocode] No results for “${locName}”`);
          }
        })
        .catch((err) => {
          // On network error, mark as failed
          setGeocodedMap((prev) => ({
            ...prev,
            [locName]: null,
          }));
          if (import.meta.env.DEV) {
            console.error(`❌ [Geocode] Error geocoding “${locName}”:`, err);
          }
        });
    });
  }, [uniqueLocations]);

  // ───────────────────────────────────────────────────────────────────────────
  // 5. Now we build an array of “finalMovements” where each object gets a real
  //    `[lat, lng]` pair: if (mv.latitude, mv.longitude) are not both 37.8/–96, use them.
  //    Otherwise, look up `geocodedMap[mv.location]`. If that also fails, fall
  //    back to [37.8, –96].
  // ───────────────────────────────────────────────────────────────────────────
  const finalMovements = React.useMemo(() => {
    return movements.map((mv) => {
      let chosenLat = mv.latitude;
      let chosenLng = mv.longitude;
      const isFallback = mv.latitude === 37.8 && mv.longitude === -96;
      if (isFallback && typeof mv.location === "string") {
        const key = mv.location.trim().toLowerCase();
        if (geocodedMap.hasOwnProperty(key) && Array.isArray(geocodedMap[key])) {
          // If we have a valid geocode, override
          [chosenLat, chosenLng] = geocodedMap[key];
        }
      }
      return {
        ...mv,
        _markerLat: chosenLat,
        _markerLng: chosenLng,
      };
    });
  }, [movements, geocodedMap]);

  // 6. Keep only those that actually got numeric coords
  const validMovements = finalMovements.filter((mv) => {
    return (
      typeof mv._markerLat === "number" &&
      typeof mv._markerLng === "number"
    );
  });

  // ───────────────────────────────────────────────────────────────────────────
  // 7. DEBUG: show how many fell out of the filter, if any.
  // ───────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (import.meta.env.DEV && finalMovements.length > 0) {
      const missingCoords = finalMovements.filter((mv) => {
        return typeof mv._markerLat !== "number" || typeof mv._markerLng !== "number";
      });
      if (missingCoords.length > 0) {
        console.warn(
          "⚠️ [MigrationMap] Still missing coords after geocoding:",
          missingCoords
        );
      } else {
        console.log(
          "✅ [MigrationMap] All finalMovements have lat/lng (count:",
          validMovements.length,
          ")"
        );
      }
    }
  }, [finalMovements, validMovements.length]);

  // ───────────────────────────────────────────────────────────────────────────
  // 8. Dynamic center: if there’s at least one valid movement, center on its coords.
  //    Otherwise fallback to [37.8, -96].
  // ───────────────────────────────────────────────────────────────────────────
  const dynamicCenter =
    validMovements.length > 0
      ? [validMovements[0]._markerLat, validMovements[0]._markerLng]
      : [37.8, -96];

  return (
    <div className="relative h-full w-full">
      <MapContainer
        key={`map-${validMovements.length}`} // remount when count changes
        center={dynamicCenter}
        zoom={4}
        scrollWheelZoom={true}
        zoomControl={false}
        style={{
          height: "100%",
          width: "100%",
          position: "relative",
          zIndex: 10,
          backgroundColor: "#101010",
        }}
        whenCreated={(mapInstance) => (mapRef.current = mapInstance)}
      >
        {/* ─────────────────────────────────────────────────────────── */}
        {/*   Tile layer (OpenStreetMap)                              */}
        {/* ─────────────────────────────────────────────────────────── */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap contributors"
        />

        {/* ─────────────────────────────────────────────────────────── */}
        {/*   Zoom control (bottom‐left)                              */}
        {/* ─────────────────────────────────────────────────────────── */}
        <ZoomControl position="bottomleft" />

        {/* ─────────────────────────────────────────────────────────── */}
        {/*   Recenter map whenever dynamicCenter changes             */}
        {/* ─────────────────────────────────────────────────────────── */}
        <RecenterMap center={dynamicCenter} />

        {/* ─────────────────────────────────────────────────────────── */}
        {/*   MARKERS: loop over validMovements and render Marker       */}
        {/* ─────────────────────────────────────────────────────────── */}
        {validMovements.map((mv, idx) => {
          const lat = mv._markerLat;
          const lng = mv._markerLng;
          const position = [lat, lng];

          // ─────────────────────────────────────────────────────────
          // Person’s name from names[0], or “Unknown”
          // ─────────────────────────────────────────────────────────
          const personName =
            Array.isArray(mv.names) && mv.names.length > 0
              ? mv.names[0]
              : "Unknown";

          // ─────────────────────────────────────────────────────────
          // Event type directly from mv.event_type
          // ─────────────────────────────────────────────────────────
          const eventType = mv.event_type || "event";

          // ─────────────────────────────────────────────────────────
          // Year parsed from mv.date (e.g. “1888-04-24” → 1888)
          // ─────────────────────────────────────────────────────────
          let year = "?";
          if (typeof mv.date === "string") {
            const parsed = new Date(mv.date);
            if (!Number.isNaN(parsed.getFullYear())) {
              year = parsed.getFullYear();
            }
          }

          // ─────────────────────────────────────────────────────────
          // Dev log: see exactly which data is used for each marker
          // ─────────────────────────────────────────────────────────
          if (import.meta.env.DEV) {
            console.log(`📌 [MigrationMap] Marker #${idx}:`, {
              event_id: mv.event_id,
              person_id: mv.person_id,
              personName,
              latitude: lat,
              longitude: lng,
              eventType,
              year,
              originalLocation: mv.location,
            });
          }

          return (
            <Marker
              key={`marker-${idx}`}
              position={position}
              icon={defaultIcon}
              eventHandlers={{
                click: () => onMarkerClick(mv.person_id),
              }}
            >
              <Popup>
                <div>
                  <strong>{personName}</strong> <br />
                  {eventType} ({year})
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* ───────────────────────────────────────────────────────────── */}
      {/*   Dev HUD: overlay showing raw vs filtered vs geocoded counts */}
      {/* ───────────────────────────────────────────────────────────── */}
      {import.meta.env.DEV && (
        <div className="absolute top-2 right-2 z-[9999] bg-black/70 text-white text-xs p-2 max-w-xs max-h-52 overflow-auto rounded shadow">
          <div>📝 Total movements fetched: {movements.length}</div>
          <div>📌 After filtering null‐coords: {finalMovements.length}</div>
          <div>🗺️ Finally displayed (valid lat/lng): {validMovements.length}</div>
          <div>🔍 Unique locations geocoded: {uniqueLocations.length}</div>
          <div>
            🌍 Geocoded map entries:{" "}
            {Object.keys(geocodedMap).filter((k) => geocodedMap[k] != null).length} /{" "}
            {uniqueLocations.length}
          </div>
          {movements.length > 0 && validMovements.length === 0 && (
            <div>⚠️ No movements have valid latitude/longitude</div>
          )}
        </div>
      )}
    </div>
  );
}
