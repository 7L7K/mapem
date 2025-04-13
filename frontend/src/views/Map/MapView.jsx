import React, { useState, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline
} from 'react-leaflet';
import { getMovements } from '../services/api';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import 'leaflet/dist/leaflet.css';
import '../styles/MapView.css';

const MapView = ({ treeId = 1 }) => {
  // Data states for movement data
  const [loading, setLoading] = useState(true);
  const [movements, setMovements] = useState([]);
  const [error, setError] = useState(null);
  const [mapReady, setMapReady] = useState(false);

  // Filter states for sidebar options
  const [selectedPerson, setSelectedPerson] = useState('');
  const [selectedEventTypes, setSelectedEventTypes] = useState({
    birth: true,
    death: true,
    residence: true,
  });
  // Default year range. You may later consider a slider component
  const [yearRange, setYearRange] = useState([1900, 2000]);
  const [filteredMovements, setFilteredMovements] = useState([]);

  // Fetch movements when treeId changes
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
        const raw = Array.isArray(res.data) ? res.data : [];
        console.log(`📦 Total movements fetched: ${raw.length}`);
  
        const missingCoords = raw.filter(e => !e.lat || !e.lng);
        if (missingCoords.length > 0) {
          console.warn(`❗ ${missingCoords.length} movement events missing lat/lng:`, missingCoords);
        }
  
        const typeCounts = raw.reduce((acc, e) => {
          const key = e.event_type || 'unknown';
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        }, {});
        console.log("📊 Event types:", typeCounts);
  
        setMovements(raw);
        setLoading(false);
        setTimeout(() => {
          setMapReady(true);
          console.log("✅ Map ready.");
        }, 10);
      })
      .catch((err) => {
        console.error("❌ Migration data load error:", err);
        setError("Migration data unavailable.");
        setLoading(false);
      });
  }, [treeId]);
  
  // Apply filters on movements
  useEffect(() => {
    const filtered = movements.filter((move) => {
      // Event type check; move.event_type should be a string
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

      // Year range check – make sure move.year is a valid number
      let yearOk = true;
      const eventYear = parseInt(move.year, 10);
      if (!isNaN(eventYear)) {
        yearOk = eventYear >= yearRange[0] && eventYear <= yearRange[1];
      }

      // Person filter – match the name if provided
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

  // Handle changes for event type toggles
  const handleEventTypeChange = (e) => {
    const { name, checked } = e.target;
    setSelectedEventTypes(prev => ({ ...prev, [name]: checked }));
  };

  return (
    <div className="map-view-container">
      {/* Sidebar Filter Panel */}
      <div className="sidebar">
        <h3>Filters</h3>
        {/* Person Search */}
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
        {/* Event Type Toggle */}
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
        {/* Year Range Inputs */}
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
        {/* Legend */}
        <div className="filter-section legend">
          <h4>Legend</h4>
          <ul>
            <li>
              <span className="legend-icon birth"></span> Birth
            </li>
            <li>
              <span className="legend-icon death"></span> Death
            </li>
            <li>
              <span className="legend-icon residence"></span> Residence
            </li>
            <li>
              <span className="legend-icon movement"></span> Movement Line
            </li>
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
              if (lat == null || lng == null) return null;
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
            {/* Draw movement lines per individual */}
            {Object.values(
              filteredMovements.reduce((acc, move) => {
                // Group movements by individual id or default to "unknown"
                const pid =
                  move.individual && move.individual.id
                    ? move.individual.id
                    : 'unknown';
                if (!acc[pid]) acc[pid] = [];
                acc[pid].push(move);
                return acc;
              }, {})
            ).map((group, idx) => {
              // Only draw lines if there are at least 2 points with valid year
              const sorted = group
                .filter(m => m.year)
                .sort((a, b) => parseInt(a.year, 10) - parseInt(b.year, 10));
              if (sorted.length > 1) {
                const positions = sorted.map(m => [m.lat, m.lng]);
                return (
                  <Polyline
                    key={`poly-${idx}`}
                    positions={positions}
                    color="#00D9FF"
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
