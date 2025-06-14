// frontend/src/features/geocode/hooks/useGeocode.js

import { useState, useEffect } from "react";
import { fetchStats, fetchUnresolved, fetchHistory } from "../api/geocodeApi";
import { devLog } from "@shared/utils/devLogger";

export default function useGeocode() {
  const [stats,      setStats]      = useState(null);
  const [unresolved, setUnresolved] = useState([]);
  const [history,    setHistory]    = useState([]);
  const [loading,    setLoading]    = useState({
    stats: true,
    unresolved: true,
    history: true,
  });

  const refreshAll = async () => {
    setLoading({ stats: true, unresolved: true, history: true });
    try {
      const [s, u, h] = await Promise.all([
        fetchStats(),
        fetchUnresolved(),
        fetchHistory(),
      ]);

      // Unwrap the double 'data' layers
      const rawStats      = s.data?.data ?? null;
      const rawUnresolved = u.data?.data ?? [];
      const rawHistory    = h.data?.data ?? [];

      devLog("useGeocode » stats:",      rawStats);
      devLog("useGeocode » unresolved:", rawUnresolved);
      devLog("useGeocode » history:",    rawHistory);

      setStats(rawStats);
      setUnresolved(Array.isArray(rawUnresolved) ? rawUnresolved : []);
      setHistory(Array.isArray(rawHistory) ? rawHistory : []);
    } catch (err) {
      console.error("🔥 useGeocode error:", err);
    } finally {
      setLoading({ stats: false, unresolved: false, history: false });
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  return { stats, unresolved, history, loading, refreshAll };
}
