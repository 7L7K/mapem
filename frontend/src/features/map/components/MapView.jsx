import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const DEFAULT_CENTER = [39.8283, -98.5795];

export default function MapView({ movements = [], loading, error }) {
  useEffect(() => {
    console.log("🗺️ Movements loaded:", movements.length);
  }, [movements]);

  if (loading) return <div className="p-6 text-dim">Loading map...</div>;
  if (error) return <div className="p-6 text-red-400">Error loading movements</div>;
  if (movements.length === 0) return <div className="p-6 text-dim">No migration data to display yet.</div>;

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={4}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
        />
        {movements.map((m, i) => (
          <Marker key={`${m.person_id}-${i}`} position={[m.latitude, m.longitude]}>
            <Popup>
              <div className="text-sm">
                <strong>{m.person_name}</strong><br />
                {m.event_type} – {m.date}<br />
                {m.location_name}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
