import React from "react";
import dayjs from "dayjs";

export default function QuickStats({ rows, loading }) {
  if (loading) {
    return <p className="text-sm text-gray-400">Loading stats…</p>;
  }

  const total = rows.length;
  const veryLow = rows.filter((r) => r.confidence <= 0.2).length;
  const lastSeen = rows.reduce(
    (max, r) => (dayjs(r.lastSeen).isAfter(max) ? dayjs(r.lastSeen) : max),
    dayjs("1900-01-01")
  );

  return (
    <div className="grid grid-cols-3 gap-4">
      <StatCard label="Unresolved" value={total} />
      <StatCard label="Low-confidence ≤ 0.2" value={veryLow} />
      <StatCard label="Last seen" value={lastSeen.format("MMM D, YYYY")} />
    </div>
  );
}

const StatCard = ({ label, value }) => (
  <div className="bg-gray-800 rounded-xl p-4 flex flex-col items-center">
    <span className="text-lg font-semibold">{value}</span>
    <span className="text-xs uppercase text-gray-400">{label}</span>
  </div>
);
