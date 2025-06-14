import React, { Suspense } from "react";
import useGeocode from "../hooks/useGeocode";
import StatsPanel from "../components/StatsPanel";
import AuditCharts from "../components/AuditCharts";
import UnresolvedTable from "../components/UnresolvedTable";
import HistoryTable from "../components/HistoryTable";

export default function GeocodeDashboardPage() {
  const { stats, unresolved, history, loading, refreshAll } = useGeocode();

  return (
    <div className="p-4 space-y-6">
      <StatsPanel
        stats={stats}
        loading={loading.stats}
        lastUpload={stats?.lastUpload}
        apiEndpoint="/api/admin/geocode/stats"
      />

      {/* AuditCharts expects array data; pass unresolved array */}
      <AuditCharts
        // was data={stats.unresolved}, now pass unresolved items array
        data={unresolved}
        loading={loading.unresolved}
      />

      {/* Unresolved table */}
      <UnresolvedTable
        data={unresolved}
        loading={loading.unresolved}
        refresh={refreshAll}
      />

      {/* History table */}
      <HistoryTable
        data={history}
        loading={loading.history}
      />
    </div>
  );
}
