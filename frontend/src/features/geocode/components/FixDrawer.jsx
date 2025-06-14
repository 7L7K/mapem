import React, { useState, useEffect } from "react";
import axios from "axios";

export default function FixDrawer({ row, onClose }) {
  console.log("🛠️ FixDrawer MOUNT", row);
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (row) {
      setLat("");
      setLng("");
      setError("");
    }
  }, [row]);

  if (!row) return null; // don’t render when no row

  const handleSave = async () => {
    if (!lat || !lng) return setError("Lat & Lng required");
    setSaving(true);
    try {
      await axios.post("/api/admin/geocode/fix", {
        id: row.id,
        lat: parseFloat(lat),
        lng: parseFloat(lng),
      });
      onClose(true);
    } catch (err) {
      setError(err?.response?.data?.error || err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "350px",
        height: "100%",
        background: "#1f2937", // Tailwind bg-gray-800
        color: "#fff",
        padding: "1rem",
        boxShadow: "-4px 0 8px rgba(0,0,0,0.5)",
        zIndex: 2000,
      }}
    >
      <h2 style={{ marginBottom: "1rem" }}>
        Fix: <span style={{ color: "#22d3ee" }}>{row.rawName}</span>
      </h2>

      <div style={{ fontSize: "0.8rem", marginBottom: "1rem" }}>
        <div><strong>ID:</strong> {row.id}</div>
        <div><strong>Events:</strong> {row.eventCount}</div>
        <div><strong>Last Seen:</strong> {new Date(row.lastSeen).toLocaleString()}</div>
      </div>

      <label style={{ fontSize: "0.75rem" }}>Latitude</label>
      <input
        type="number"
        step="any"
        value={lat}
        onChange={(e) => setLat(e.target.value)}
        style={{
          width: "100%",
          margin: "0.5rem 0",
          padding: "0.5rem",
          borderRadius: "0.25rem",
          border: "1px solid #374151",
          background: "#374151",
          color: "#fff",
        }}
        disabled={saving}
      />

      <label style={{ fontSize: "0.75rem" }}>Longitude</label>
      <input
        type="number"
        step="any"
        value={lng}
        onChange={(e) => setLng(e.target.value)}
        style={{
          width: "100%",
          margin: "0.5rem 0 1rem",
          padding: "0.5rem",
          borderRadius: "0.25rem",
          border: "1px solid #374151",
          background: "#374151",
          color: "#fff",
        }}
        disabled={saving}
      />

      {error && (
        <div style={{ marginBottom: "1rem", color: "#f87171" }}>
          {error}
        </div>
      )}

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            flex: 1,
            padding: "0.5rem",
            background: "#06b6d4",
            borderRadius: "0.25rem",
            color: "#000",
            fontWeight: "600",
          }}
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          onClick={() => onClose(false)}
          disabled={saving}
          style={{
            flex: 1,
            padding: "0.5rem",
            background: "#374151",
            borderRadius: "0.25rem",
            color: "#fff",
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
