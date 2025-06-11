import React from 'react';
import StatsPanel from '../components/StatsPanel';
import BatchControls from '../components/BatchControls';
import AuditCharts from '../components/AuditCharts';
import UnresolvedTable from '../components/UnresolvedTable';
import FixModal from '../components/FixModal';
import HistoryTable from '../components/HistoryTable';
import useGeocode from '../hooks/useGeocode';

export default function GeocodeDashboardPage() {
  const { stats, unresolved, history, loading, refreshAll } = useGeocode();

  return (
    <div className="p-6 space-y-8">
      <StatsPanel    stats={stats}           loading={loading.stats}      />
      <BatchControls onActionComplete={refreshAll}                          />
      <AuditCharts   stats={stats}           unresolved={unresolved}      />
      <UnresolvedTable 
        data={unresolved} 
        loading={loading.unresolved} 
        refresh={refreshAll} 
      />
      <FixModal      onSuccess={refreshAll}                                 />
      <HistoryTable  data={history}      loading={loading.history}         />
    </div>
  );
}
