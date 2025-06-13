// frontend/src/features/geocode/components/HistoryTable.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";
import { devLog } from "@shared/utils/devLogger";

export default function HistoryTable() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ start: "", end: "" });

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    const reqId = Math.random().toString(36).slice(2);
    devLog("HistoryTable", `🔄 [${reqId}] Fetching history`);
    try {
      const { data } = await axios.get("/admin/geocode/history");
      setHistory(data);
      devLog("HistoryTable", `✅ [${reqId}] Got history`, data.length);
    } catch (err) {
      devLog("HistoryTable", `❌ [${reqId}] fetch failed`, err);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    const headers = ["ID", "Raw Name", "Lat", "Lng", "Fixed By", "Date"];
    const rows = filtered.map(h => [
      h.id,
      h.rawName,
      h.lat,
      h.lng,
      h.fixedBy,
      new Date(h.date).toLocaleString(),
    ]);
    let csv =
      headers.join(",") +
      "\n" +
      rows.map(r => r.map(v => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "geocode_history.csv";
    a.click();
    URL.revokeObjectURL(url);
    devLog("HistoryTable", "📥 CSV exported", rows.length);
  };

  const filtered = history.filter(h => {
    if (!filter.start && !filter.end) return true;
    const d = new Date(h.date);
    if (filter.start && d < new Date(filter.start)) return false;
    if (filter.end && d > new Date(filter.end)) return false;
    return true;
  });

  if (loading) return <p>Loading history...</p>;

  return (
    <div>
      <div className="flex items-center space-x-4 mb-4">
        <div>
          <label>Start:</label>
          <input
            type="date"
            value={filter.start}
            onChange={e => setFilter({ ...filter, start: e.target.value })}
            className="ml-2 border rounded p-1"
          />
        </div>
        <div>
          <label>End:</label>
          <input
            type="date"
            value={filter.end}
            onChange={e => setFilter({ ...filter, end: e.target.value })}
            className="ml-2 border rounded p-1"
          />
        </div>
        <button
          onClick={exportCSV}
          className="ml-auto px-3 py-1 bg-green-600 text-white rounded"
        >
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white">
          <thead>
            <tr>
              {["ID", "Raw Name", "Lat", "Lng", "Fixed By", "Date"].map(col => (
                <th key={col} className="px-4 py-2 border text-left">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(row => (
              <tr
                key={row.id}
                className="hover:bg-gray-100 cursor-pointer"
                onClick={() => devLog("HistoryTable", "👁️ row click", row)}
              >
                <td className="px-4 py-2 border">{row.id}</td>
                <td className="px-4 py-2 border">{row.rawName}</td>
                <td className="px-4 py-2 border">{row.lat}</td>
                <td className="px-4 py-2 border">{row.lng}</td>
                <td className="px-4 py-2 border">{row.fixedBy}</td>
                <td className="px-4 py-2 border">
                  {new Date(row.date).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
