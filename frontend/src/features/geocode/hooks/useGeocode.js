import { useState, useEffect } from "react";
import {
  fetchStats,
  fetchUnresolved,
  fetchHistory,
} from "../api/geocodeApi";

export default function useGeocode() {
  const [stats, setStats] = useState(null);
  const [unresolved, setUnresolved] = useState([]);
  const [history, setHistory]    = useState([]);
  const [loading, setLoading] = useState({
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
      setStats(s.data);
      setUnresolved(u.data);
      setHistory(h.data);
    } catch (err) {
      console.error("🔥 useGeocode error:", err);
    } finally {
      setLoading({ stats: false, unresolved: false, history: false });
    }
  };

  useEffect(() => { refreshAll(); }, []);

  return { stats, unresolved, history, loading, refreshAll };
}
