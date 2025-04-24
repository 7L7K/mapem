import React from "react";

export default function Legend({ movements = [], className = "" }) {
  const eventTypes = Array.from(new Set(movements.map((m) => m.event_type)));

  return (
    <div className={`bg-surface text-text border border-border rounded-md shadow-md p-4 ${className}`}>
      <h3 className="text-sm font-semibold mb-2">Legend</h3>
      <ul className="space-y-1 text-sm text-dim">
        {eventTypes.map((type) => (
          <li key={type}>• {type}</li>
        ))}
      </ul>
    </div>
  );
}
