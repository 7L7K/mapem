import React from "react";

const Legend = ({ movements = [] }) => {
  const eventCounts = movements.reduce((acc, m) => {
    const type = (m.event_type || "unknown").toLowerCase();
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  const uniquePeople = new Set(movements.map(m => m.person_id));
  const yearRange = movements
    .map(m => parseInt(m.year))
    .filter(y => !isNaN(y))
    .reduce(
      (acc, y) => {
        acc.min = Math.min(acc.min, y);
        acc.max = Math.max(acc.max, y);
        return acc;
      },
      { min: Infinity, max: -Infinity }
    );

  return (
    <div className="text-sm space-y-1">
      <p>🧍 People: <strong>{uniquePeople.size}</strong></p>
      <p>📍 Events: <strong>{movements.length}</strong></p>
      {Object.entries(eventCounts).map(([type, count]) => (
        <p key={type}>• {type.charAt(0).toUpperCase() + type.slice(1)}: {count}</p>
      ))}
      {yearRange.min !== Infinity && (
        <p>📅 Years: {yearRange.min}–{yearRange.max}</p>
      )}
    </div>
  );
};

export default Legend;
