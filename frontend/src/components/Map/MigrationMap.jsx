// frontend/src/components/Map/MigrationMap.jsx
import React, { useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// 🛠️ Marker icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

// 🌈 Person color palette
const colorForPerson = (id) => {
  const palette = [
    '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#6366f1',
    '#14b8a6', '#a855f7', '#f97316', '#0ea5e9', '#ec4899',
  ];
  return palette[id % palette.length];
};

// 🧭 Auto-center map on data change
const AutoCenter = ({ center }) => {
  const map = useMap();

  useEffect(() => {
    console.log("🧭 [MigrationMap] Re-centering map to:", center);
    map.setView(center, map.getZoom());
  }, [center, map]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      requestAnimationFrame(() => {
        try {
          console.log("🔁 [MigrationMap] Forcing map redraw (invalidateSize)");
          map.invalidateSize();
        } catch (err) {
          console.warn("❌ [MigrationMap] invalidateSize failed:", err);
        }
      });
    }, 500);

    return () => clearTimeout(timeout);
  }, [map]);

  return null;
};

// 📍 Main Map Component
const MigrationMap = ({ movements = [], center = [37, -95], onMarkerClick, activePersonIds = new Set() }) => {
  useEffect(() => {
    console.log("🗺️ [MigrationMap] Rendering with", movements.length, "movements");
    window.__MAP_PERSON_NAMES__ = movements.map((m) => m.person_name);
  }, [movements]);

  const renderKey = movements.length || 0; // ✅ now inside the component and scoped correctly
  console.log('%c[MigrationMap] RETURNING MAPCONTAINER...', 'color:lime');

  return (
    <MapContainer
      key={`map-${renderKey}`}
      center={center}
      zoom={4}
      scrollWheelZoom={true}
      style={{ height: '100%', width: '100%',position: 'relative', zIndex: 10,backgroundColor: '#101010', }}
      whenCreated={(map) => {
        console.log('%c[MigrationMap] Leaflet map instance created:', 'color:green', map);
        map.on('load', () => console.log('%c[MigrationMap] TileLayer load event fired', 'color:green'));
        map.on('tileerror', (err) => console.error('%c[MigrationMap] Tile error:', 'color:red', err));
      }}
    >
      <AutoCenter center={center} />

      <TileLayer
        attribution='© OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        eventHandlers={{
          tileload: () => console.log('%c[TileLayer] tile loaded', 'color:blue'),
        }}
      />

      {movements.map((move, idx) => {
        const { latitude, longitude, person_id, person_name, event_type, year, prev_lat, prev_lng } = move;
        const isValid = latitude && longitude;

        if (!isValid) {
          console.warn(`⚠️ Skipping invalid lat/lng for movement[${idx}]`, move);
          return null;
        }

        const color = colorForPerson(person_id);
        const isActive = activePersonIds.has(person_id);

        return (
          <React.Fragment key={idx}>
            <Marker
              position={[latitude, longitude]}
              eventHandlers={{
                click: () => {
                  console.log(`🟡 [Marker Clicked]`, person_name, latitude, longitude);
                  onMarkerClick?.(person_id);
                },
              }}
            >
              <Popup>
                <div>
                  <strong>{person_name}</strong><br />
                  {event_type} ({year})
                </div>
              </Popup>
            </Marker>

            {prev_lat && prev_lng && (
              <Polyline
                positions={[[prev_lat, prev_lng], [latitude, longitude]]}
                pathOptions={{
                  color,
                  weight: isActive ? 5 : 2,
                  opacity: isActive ? 1 : 0.6,
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </MapContainer>
  );
};

export default MigrationMap;
