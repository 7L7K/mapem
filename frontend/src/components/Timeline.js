// Timeline component
import React, { useState, useEffect } from 'react';

const Timeline = () => {
  const [versions, setVersions] = useState([]);

  useEffect(() => {
    // Simulated timeline data; replace with an API call if needed.
    const simulatedData = [
      { id: 1, version: 1, created_at: '2023-01-01T12:00:00Z' },
      { id: 2, version: 2, created_at: '2023-02-01T12:00:00Z' },
      { id: 3, version: 3, created_at: '2023-03-01T12:00:00Z' }
    ];
    setVersions(simulatedData);
  }, []);

  return (
    <div>
      <h2>Timeline</h2>
      <ul>
        {versions.map(v => (
          <li key={v.id}>
            Version {v.version} - {new Date(v.created_at).toLocaleString()}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Timeline;
