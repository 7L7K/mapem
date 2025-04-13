// components/MigrationMap.jsx
import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MigrationMap = ({ movements }) => {
  const displayMovements = movements.length > 0
    ? movements
    : [
        { name: 'John', lat: 40.7128, lng: -74.0060, year: 1910 },
        { name: 'Mary', lat: 34.0522, lng: -118.2437, year: 1930 }
      ];

  return (
    <MapContainer
      center={[39.8283, -98.5795]}
      zoom={4}
      scrollWheelZoom={false}
      style={{ height: '600px', width: '100%' }}
      key={JSON.stringify(displayMovements)} // ensures unmount on data change
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {displayMovements.map((move, index) => {
        const { lat, lng, name, year } = move;
        if (!lat || !lng) return null;
        return (
          <Marker key={index} position={[lat, lng]}>
            <Popup>
              <strong>{name || 'Unknown'}</strong><br />
              {year ? `Year: ${year}` : 'No year provided'}
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
};

export default MigrationMap;
