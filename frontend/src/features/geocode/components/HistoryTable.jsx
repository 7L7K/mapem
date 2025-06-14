import React, { useState } from "react";
import PropTypes from "prop-types";
import { devLog } from "@shared/utils/devLogger";

export default function HistoryTable({ data = [], loading }) {
  const [filter, setFilter] = useState({ start: "", end: "" });

  const rows = Array.isArray(data) ? data : [];

  /* ---------- CSV ---------- */
  const exportCSV = () => {
    const headers = ["ID", "Raw Name", "Lat", "Lng", "Date Fixed"];
    const csvRows = rows.map(r => [
      r.id,
      r.raw_name,
      r.latitude,
      r.longitude,
      new Date(r.fixed_at).toLocaleString(),
    ]);
    const csv =
      headers.join(",") +
      "\n" +
      csvRows.map(r => r.map(v => `"${v ?? ""}"`).join(",")).join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url;
    a.download = "geocode_history.csv";
    a.click();
    URL.revokeObjectURL(url);
    devLog("HistoryTable", "📥 CSV exported", csvRows.length);
  };

  /* ---------- Filter ---------- */
  const filtered = rows.filter(r => {
    if (!filter.start && !filter.end) return true;
    const d = new Date(r.fixed_at);
    if (filter.start && d < new Date(filter.start)) return false;
    if (filter.end   && d > new Date(filter.end))   return false;
    return true;
  });

  if (loading) return <p>Loading history…</p>;

  /* ---------- UI ---------- */
  return (
    <div>
      {/* Date filter + export */}
      <div className="flex items-center space-x-4 mb-4">
        {["start", "end"].map(k => (
          <label key={k} className="space-x-2">
            <span>{k === "start" ? "Start" : "End"}:</span>
            <input
              type="date"
              value={filter[k]}
              onChange={e => setFilter({ ...filter, [k]: e.target.value })}
              className="border rounded p-1"
            />
          </label>
        ))}

        <button
          onClick={exportCSV}
          className="ml-auto px-3 py-1 bg-green-600 text-white rounded"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white">
          <thead>
            <tr>
              {["ID", "Raw Name", "Lat", "Lng", "Date Fixed"].map(col => (
                <th key={col} className="px-4 py-2 border text-left">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => (
              <tr
                key={r.id}
                className="hover:bg-gray-100 cursor-pointer"
                onClick={() => devLog("HistoryTable", "👁️ row click", r)}
              >
                <td className="px-4 py-2 border">{r.id}</td>
                <td className="px-4 py-2 border">{r.raw_name}</td>
                <td className="px-4 py-2 border">{r.latitude}</td>
                <td className="px-4 py-2 border">{r.longitude}</td>
                <td className="px-4 py-2 border">
                  {new Date(r.fixed_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

HistoryTable.propTypes = {
  data:    PropTypes.array,
  loading: PropTypes.bool,
};
