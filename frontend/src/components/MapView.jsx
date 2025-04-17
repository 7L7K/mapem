import React, { useState, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline
} from 'react-leaflet';
import { getMovements } from '../services/api';
import { useTree } from '../context/TreeContext';

import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import 'leaflet/dist/leaflet.css';
import '../styles/MapView.css';


// 🎨 Generates a consistent color per person
const getColorForId = (id) => {
  const colors = [
    "#FF5733", "#33C1FF", "#8D33FF", "#33FF57", "#FFD433",
    "#FF33A8", "#33FFF5", "#B833FF", "#33FFBD", "#FF7E33"
  ];
  return colors[id % colors.length];
};

const MapView = () => {
  const { treeId } = useTree(); // 👈 this is now reactive!
  console.log("🌲 [Debug] treeId from context:", treeId);
  const [loading, setLoading] = useState(true);
  const [movements, setMovements] = useState([]);
  const [error, setError] = useState(null);
  const [mapReady, setMapReady] = useState(false);

  const [selectedPerson, setSelectedPerson] = useState('');
  const [selectedEventTypes, setSelectedEventTypes] = useState({
    birth: true,
    death: true,
    residence: true,
  });
  const [yearRange, setYearRange] = useState([1900, 2000]);
  const [filteredMovements, setFilteredMovements] = useState([]);
//

  useEffect(() => {
    if (!treeId || isNaN(treeId)) {
      console.warn("⚠️ Invalid treeId provided to MapView:", treeId);
      return;
    }

    setLoading(true);
    setMapReady(false);
    console.log("📡 Fetching migration data for treeId:", treeId);

    getMovements(treeId)
      .then((res) => {
        console.log("🌐 [API] GET /api/movements/" + treeId);
        console.log("📬 [Debug] Raw response from getMovements:", res);
        const raw = Array.isArray(res) ? res : [];
        console.log("📦 [Debug] Parsed raw person list:", raw);
        
        const flattened = raw.flatMap(person =>
          person.movements.map(movement => ({
            ...movement,
            lat: movement.latitude,
            lng: movement.longitude,
            name: person.person_name,
            individual: {
              id: person.person_id,
              name: person.person_name
            }
          }))
        );

        console.log(`📉 [Debug] Flattened movement count: ${flattened.length}`);
        console.log("🧭 [Debug] First few movements:", flattened.slice(0, 3));      

        const missingCoords = flattened.filter(e => !e.lat || !e.lng);
        if (missingCoords.length > 0) {
          console.warn(`❗ ${missingCoords.length} movement events missing lat/lng:`, missingCoords);
        }

        const typeCounts = flattened.reduce((acc, e) => {
          const key = e.event_type || 'unknown';
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        }, {});
        console.log("📊 Event types:", typeCounts);

        setMovements(flattened);
        setFilteredMovements(flattened);
        setLoading(false);
        setTimeout(() => {
          setMapReady(true);
          console.log("✅ Map ready.");
        }, 10);
      })
      .catch((err) => {
        console.error("❌ Migration data load error:", err);
        setError("Migration data unavailable.");
        setFilteredMovements([]);
        setLoading(false);
      });
  }, [treeId]);

  useEffect(() => {
    const filtered = movements.filter((move) => {
      let typeOk = false;
      if (typeof move.event_type === 'string') {
        const et = move.event_type.toLowerCase();
        if (et.includes('birth') && selectedEventTypes.birth) {
          typeOk = true;
        } else if (et.includes('death') && selectedEventTypes.death) {
          typeOk = true;
        } else if (
          (et.includes('residence') || et.includes('migration')) &&
          selectedEventTypes.residence
        ) {
          typeOk = true;
        }
      }

      let yearOk = true;
      const eventYear = parseInt(move.year, 10);
      if (!isNaN(eventYear)) {
        yearOk = eventYear >= yearRange[0] && eventYear <= yearRange[1];
      }

      let personOk = true;
      if (
        selectedPerson.trim() &&
        move.individual &&
        typeof move.individual.name === 'string'
      ) {
        personOk = move.individual.name
          .toLowerCase()
          .includes(selectedPerson.toLowerCase());
      }

      return typeOk && yearOk && personOk;
    });
    setFilteredMovements(filtered);
  }, [movements, selectedEventTypes, yearRange, selectedPerson]);

  const handleEventTypeChange = (e) => {
    const { name, checked } = e.target;
    setSelectedEventTypes(prev => ({ ...prev, [name]: checked }));
  };

  return (
    <div className="map-view-container">
      {/* Sidebar Filter Panel */}
      <div className="sidebar">
        <h3>Filters</h3>
        <div className="filter-section">
          <label>
            <strong>Person:</strong>
            <input
              type="text"
              placeholder="Search by name..."
              value={selectedPerson}
              onChange={(e) => setSelectedPerson(e.target.value)}
            />
          </label>
        </div>
        <div className="filter-section">
          <h4>Event Types</h4>
          <label>
            <input
              type="checkbox"
              name="birth"
              checked={selectedEventTypes.birth}
              onChange={handleEventTypeChange}
            />
            Births
          </label>
          <br />
          <label>
            <input
              type="checkbox"
              name="death"
              checked={selectedEventTypes.death}
              onChange={handleEventTypeChange}
            />
            Deaths
          </label>
          <br />
          <label>
            <input
              type="checkbox"
              name="residence"
              checked={selectedEventTypes.residence}
              onChange={handleEventTypeChange}
            />
            Residences
          </label>
        </div>
        <div className="filter-section">
          <h4>Year Range</h4>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="number"
              value={yearRange[0]}
              onChange={(e) =>
                setYearRange([parseInt(e.target.value, 10), yearRange[1]])
              }
              min="1800"
              max={yearRange[1]}
            />
            <span>to</span>
            <input
              type="number"
              value={yearRange[1]}
              onChange={(e) =>
                setYearRange([yearRange[0], parseInt(e.target.value, 10)])
              }
              min={yearRange[0]}
              max="2025"
            />
          </div>
        </div>
        <div className="filter-section legend">
          <h4>Legend</h4>
          <ul>
            <li><span className="legend-icon birth"></span> Birth</li>
            <li><span className="legend-icon death"></span> Death</li>
            <li><span className="legend-icon residence"></span> Residence</li>
            <li><span className="legend-icon movement"></span> Movement Line</li>
          </ul>
        </div>
      </div>

      {/* Map Container */}
      <div className="map-container">
        {loading && <Loader />}
        {error && <ErrorBox message={error} />}
        {mapReady && (
          <MapContainer
            center={[39.8283, -98.5795]}
            zoom={4}
            scrollWheelZoom={true}
            style={{ height: '600px', width: '100%' }}
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filteredMovements.map((move, idx) => {
              const { lat, lng, name, year } = move;
              if (lat == null || lng == null) {
                console.warn("❌ [Skipped] Missing coordinates for:", move);
                return null;
              }
              
              console.log("📍 [Render] Marker for:", {
                idx,
                lat,
                lng,
                name,
                year
              });
              
              return (
                <Marker key={idx} position={[lat, lng]}>
                                <Popup>
                    <strong>{name || 'Unknown'}</strong>
                    <br />
                    {year ? `Year: ${year}` : 'No year provided'}
                  </Popup>
                </Marker>
              );
            })}
            {Object.values(
              filteredMovements.reduce((acc, move) => {
                const pid = move.individual?.id ?? 'unknown';
                if (!acc[pid]) acc[pid] = [];
                acc[pid].push(move);
                return acc;
              }, {})
            ).map((group, idx) => {
              const sorted = group
                .filter(m => m.year && m.lat && m.lng)
                .sort((a, b) => parseInt(a.year, 10) - parseInt(b.year, 10));
              if (sorted.length > 1) {
                const positions = sorted.map(m => [m.lat, m.lng]);
                return (
                  <Polyline
                    key={`poly-${idx}`}
                    positions={positions}
                    color={getColorForId(group[0].individual?.id ?? idx)}
                  />
                );
              }
              return null;
            })}
          </MapContainer>
        )}
      </div>
    </div>
  );
};

export default MapView;
