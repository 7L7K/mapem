import React from 'react';

export default function GeocodeDashboardPage() {
  return (
    <iframe
      src="http://localhost:5050/admin/geocode"
      title="Geocode Dashboard"
      style={{
        width: '100%',
        height: '100vh',
        border: 'none'
      }}
    />
  );
}
