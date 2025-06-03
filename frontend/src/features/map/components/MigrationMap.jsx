import React, { useRef, useEffect } from "react";
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

const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && Array.isArray(center)) {
      map.setView(center, map.getZoom());
      if (import.meta.env.DEV)
        console.log("🧭 [MigrationMap] Re-centering map to:", center);
    }
  }, [center, map]);
  return null;
}

export default function MigrationMap({
  movements = [],
  center = [37.8, -96],
  onMarkerClick = () => {},
  activePersonIds = new Set(),
}) {
  const mapRef = useRef(null);

  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
        if (import.meta.env.DEV)
          console.log("🔁 [MigrationMap] Forcing map redraw (invalidateSize)");
      }, 200);
    }
  }, []);

  return (
    <MapContainer
      key={`map-${movements.length}`}
      center={center}
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
      {/* 🔍 Tiles */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap contributors"
      />

      {/* 🔍 Zoom Control: now bottom-left */}
      <ZoomControl position="bottomleft" />

      {/* 🔁 Keep map centered */}
      <RecenterMap center={center} />

      {/* 📍 Markers */}
      {movements.map((mv, idx) => {
        if (!mv.latitude || !mv.longitude) return null;

        const position = [mv.latitude, mv.longitude];
        const isActive = activePersonIds.has(mv.person_id);

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
                <strong>{mv.person_name}</strong> <br />
                {mv.event_type} ({mv.year})
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
