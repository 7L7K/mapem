/**
 * geocodeApi.js
 * Central wrapper for Geocode Dashboard API.
 * Exports all named funcs so hooks/components can import cleanly.
 * /Users/kingal/mapem/frontend/src/features/geocode/api/geocodeApi.js
 */


const API_ROOT = import.meta.env.VITE_BACKEND_URL ?? "/api/admin/geocode";

/** Shared fetch + error handling */
async function _request(path, opts = {}) {
  try {
    const res = await fetch(`${API_ROOT}${path}`, {
      credentials: "include",
      ...opts,
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = await res.json();
    return { data: json, error: null };
  } catch (error) {
    console.error("🛑 geocodeApi error:", error);
    return { data: null, error };
  }
}

// ————— TOP SUMMARY —————
export function fetchStats() {
  return _request("/stats");
}

// ————— UNRESOLVED TABLE —————
export function fetchUnresolved(params = {}) {
  const q = new URLSearchParams(params).toString();
  return _request(`/unresolved?${q}`);
}

// ————— HISTORY TABLE —————
export function fetchHistory(params = {}) {
  const q = new URLSearchParams(params).toString();
  return _request(`/history?${q}`);
}

// ————— ACTIONS —————
export function manualFix(id, lat, lng) {
  return _request(`/fix/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng }),
  });
}
export function retryUnresolved(id) {
  return _request(`/retry/${id}`, { method: "POST" });
}

// Optional default export for convenience
export default {
  fetchStats,
  fetchUnresolved,
  fetchHistory,
  manualFix,
  retryUnresolved,
};
