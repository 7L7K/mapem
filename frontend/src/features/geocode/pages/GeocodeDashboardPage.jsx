// frontend/src/features/geocode/pages/GeocodeDashboardPage.jsx
import React, { useState } from 'react';
import StatsPanel from '../components/StatsPanel';
import BatchControls from '../components/BatchControls';
import AuditCharts from '../components/AuditCharts';
import UnresolvedTable from '../components/UnresolvedTable';
import FixModal from '../components/FixModal';
import HistoryTable from '../components/HistoryTable';
import useGeocode from "../hooks/useGeocode";
import { devLog } from "@shared/utils/devLogger";

export default function GeocodeDashboardPage() {
  const { stats, unresolved, history, loading, refreshAll } = useGeocode();

  const [selectedLocationId, setSelectedLocationId] = useState(null);

  devLog("📊 Dashboard Data:", { stats, unresolved, history, loading });

  return (
    <div className="p-6 space-y-8">
      <StatsPanel 
        apiEndpoint="/api/geocode/stats" 
        stats={stats || null} 
        loading={loading?.stats || false} 
      />

      <BatchControls onActionComplete={refreshAll} />

      <AuditCharts 
        stats={stats || null} 
        onFilter={(key) => devLog("🔍 Filter clicked:", key)} 
      />

      <UnresolvedTable 
        data={unresolved || []} 
        loading={loading?.unresolved || false} 
        refresh={refreshAll} 
        onSelect={(id) => setSelectedLocationId(id)}
      />

      {selectedLocationId && (
        <FixModal
          isOpen={true}
          onClose={() => setSelectedLocationId(null)}
          locationId={selectedLocationId}
          onSuccess={() => {
            setSelectedLocationId(null);
            refreshAll();
          }}
        />
      )}

      <HistoryTable 
        data={history || []} 
        loading={loading?.history || false} 
      />
    </div>
  );
}
