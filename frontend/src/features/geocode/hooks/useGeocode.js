// src/features/geocode/api/geocodeApi.js
const API_ROOT = import.meta.env.VITE_BACKEND_URL ?? "/api/admin/geocode";

async function _request(path, opts = {}) {
  try {
    const res = await fetch(`${API_ROOT}${path}`, {
      credentials: "include",
      ...opts,
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = await res.json();
    return { data: json, error: null };
  } catch (err) {
    console.error("🛑 geocodeApi error:", err);
    return { data: null, error: err };
  }
}

export const fetchStats = () => _request("/stats");

export const fetchUnresolved = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return _request(`/unresolved?${query}`);
};

export const fetchHistory = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return _request(`/history?${query}`);
};

export const manualFix = (id, lat, lng) =>
  _request(`/fix/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng }),
  });

export const retryUnresolved = (id) =>
  _request(`/retry/${id}`, { method: "POST" });

export default {
  fetchStats,
  fetchUnresolved,
  fetchHistory,
  manualFix,
  retryUnresolved,
};
