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

// Ensure marker icons show up
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

const colorForPerson = (id) => {
  const palette = [
    '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#6366f1',
    '#14b8a6', '#a855f7', '#f97316', '#0ea5e9', '#ec4899',
  ];
  return palette[id % palette.length];
};

// Optional: Reset zoom/center when movements update
const AutoCenter = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
};

const MigrationMap = ({ movements = [], center = [37, -95], onMarkerClick, activePersonIds = new Set() }) => {
  useEffect(() => {
    window.__MAP_PERSON_NAMES__ = movements.map((m) => m.person_name);
  }, [movements]);

  return (
    <MapContainer center={center} zoom={4} style={{ height: '100%', width: '100%' }}>
      <AutoCenter center={center} />
      <TileLayer
        attribution='© OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {movements.map((move, idx) => {
        const color = colorForPerson(move.person_id);
        const isActive = activePersonIds.has(move.person_id);

        return (
          <React.Fragment key={idx}>
            <Marker
              position={[move.latitude, move.longitude]}
              eventHandlers={{
                click: () => onMarkerClick?.(move.person_id),
              }}
            >
              <Popup>
                <div>
                  <strong>{move.person_name}</strong><br />
                  {move.event_type} ({move.year})
                </div>
              </Popup>
            </Marker>

            {move.prev_lat && move.prev_lng && (
              <Polyline
                positions={[[move.prev_lat, move.prev_lng], [move.lat, move.lng]]}
                pathOptions={{ color, weight: isActive ? 5 : 2, opacity: isActive ? 1 : 0.6 }}
              />
            )}
          </React.Fragment>
        );
      })}
    </MapContainer>
  );
};

export default MigrationMap;
