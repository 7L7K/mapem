// /Users/kingal/mapem/frontend/src/features/geocode/api/geocodeApi.js

/**
 * Geocode API wrapper
 * Handles fetch calls + error tracking for admin/geocode dashboard.
 */

const API_ROOT = import.meta.env.VITE_BACKEND_URL ?? "/api/admin/geocode";

/** Core request wrapper with basic error handling */
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
    console.error("🛑 [geocodeApi] error:", error);
    return { data: null, error };
  }
}

// ─────────────────────────────────────────
// 📊 DASHBOARD METRICS
// ─────────────────────────────────────────

export function fetchStats() {
  return _request("/stats");
}

// ─────────────────────────────────────────
// 🧩 UNRESOLVED LOCATION ENTRIES
// ─────────────────────────────────────────

export function fetchUnresolved(params = {}) {
  const q = Object.keys(params).length
    ? `?${new URLSearchParams(params).toString()}`
    : "";
  return _request(`/unresolved${q}`);
}

export function retryUnresolved(id) {
  return _request(`/retry/${id}`, { method: "POST" });
}

// ─────────────────────────────────────────
// 📝 MANUAL FIX HISTORY + ACTIONS
// ─────────────────────────────────────────

export function fetchHistory(params = {}) {
  const q = Object.keys(params).length
    ? `?${new URLSearchParams(params).toString()}`
    : "";
  return _request(`/history${q}`);
}

export function manualFix(id, lat, lng) {
  return _request(`/fix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, lat, lng }),
  });
}

// ─────────────────────────────────────────
// ✨ Optional default export for convenience
// ─────────────────────────────────────────

export default {
  fetchStats,
  fetchUnresolved,
  fetchHistory,
  manualFix,
  retryUnresolved,
};
