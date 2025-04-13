// src/components/SchemaViewer.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

function SchemaViewer() {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("📡 Fetching DB schema from:", `${API_BASE_URL}/api/schema`);
    axios.get(`${API_BASE_URL}/api/schema`)
      .then((res) => {
        setSchema(res.data);
        console.log("✅ Schema fetched:", res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("❌ Error fetching schema:", err);
        setError("Failed to fetch schema.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>🌀 Loading schema...</div>;
  if (error) return <div style={{ color: 'red', padding: '1rem' }}>{error}</div>;

  return (
    <div style={{ padding: '1rem' }}>
      <h2>🧬 Database Schema</h2>
      {schema && Object.keys(schema).map((table) => (
        <div key={table} style={{ marginBottom: '1rem', border: '1px solid #ccc', padding: '0.5rem' }}>
          <h3>{table}</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={cellStyle}>Name</th>
                <th style={cellStyle}>Type</th>
                <th style={cellStyle}>Nullable</th>
                <th style={cellStyle}>Default</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(schema[table]) && schema[table].map((col) => (
                <tr key={col.name}>
                  <td style={cellStyle}>{col.name}</td>
                  <td style={cellStyle}>{col.type}</td>
                  <td style={cellStyle}>{col.nullable ? "Yes" : "No"}</td>
                  <td style={cellStyle}>{col.default || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

const cellStyle = {
  border: '1px solid #ccc',
  padding: '0.5rem',
  textAlign: 'left'
};

export default SchemaViewer;
