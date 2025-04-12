import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MapView = () => {
  const [geojsonData, setGeojsonData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch GeoJSON data from the backend
  useEffect(() => {
    const fetchGeoJSON = async () => {
      try {
        console.log("🧠 Fetching GeoJSON data...");
        const response = await fetch('/data/residences.geojson');
        if (!response.ok) {
          throw new Error(`Failed to fetch GeoJSON: ${response.statusText}`);
        }
        const data = await response.json();
        console.log(`📌 GeoJSON data fetched successfully: ${data.features.length} features`);
        setGeojsonData(data);
      } catch (err) {
        console.error("💥 Error loading GeoJSON:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchGeoJSON();
  }, []);

  if (loading) {
    return <div>Loading map...</div>;
  }

  if (error) {
    return <div>Error loading map: {error}</div>;
  }

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <MapContainer center={[32.9715285, -89.7348497]} zoom={6} style={{ height: '100%' }}>
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {geojsonData && (
          <GeoJSON data={geojsonData} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapView;
