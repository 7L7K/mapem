import React, { useState, useEffect } from "react";
import axios from "axios";
import UnresolvedTable from "./components/UnresolvedTable";
import QuickStats from "./components/QuickStats";
import FixDrawer from "./components/FixDrawer";
import { devLog } from "@shared/utils/devLogger";

export default function GeocodeDashboard() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drawerRow, setDrawerRow] = useState(null);   // null = closed

  const fetchRows = async () => {
    const reqId = Math.random().toString(36).slice(2);
    devLog("GeocodeDashboard", `🔄 [${reqId}] fetch unresolved`);
    try {
      const { data } = await axios.get("/api/admin/geocode/unresolved");
      setRows(data.data ?? []);
      devLog("GeocodeDashboard", `✅ [${reqId}] rows:`, data.data?.length);
    } catch (err) {
      devLog("GeocodeDashboard", `❌ fetch failed`, err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, []);

  const handleFix = (row) => setDrawerRow(row);
  const handleDrawerClose = (updated) => {
    if (updated) fetchRows(); // refresh after save
    setDrawerRow(null);
  };

  return (
    <section className="p-4 space-y-6">
      <QuickStats rows={rows} loading={loading} />
      <UnresolvedTable
        rows={rows}
        loading={loading}
        onFixClick={handleFix}
      />
      <FixDrawer row={drawerRow} onClose={handleDrawerClose} />
    </section>
  );
}
