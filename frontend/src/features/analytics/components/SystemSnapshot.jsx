import React, { useEffect, useState } from 'react';
import { Card } from '@shared/components/ui/Card';
import { getSystemSnapshot } from '@lib/api/api';
import usePerformance from '@hooks/usePerformance';

export default function SystemSnapshot() {
  usePerformance('SystemSnapshot', []);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSystemSnapshot()
      .then(setStats)
      .catch(err => {
        console.error('Snapshot fetch failed', err);
        setError('Failed to load system snapshot');
      });
  }, []);

  if (error) {
    return <Card className="text-red-300">{error}</Card>;
  }

  if (!stats) {
    return <Card>Loading snapshot...</Card>;
  }

  const entries = [
    { label: 'Total Locations', value: stats.total_locations },
    { label: 'Resolved (OK)', value: stats.resolved },
    { label: 'Unresolved', value: stats.unresolved },
    { label: 'Manual Fixes', value: stats.manual_fixes },
    { label: 'Failed', value: stats.failed },
  ];

  return (
    <Card className="space-y-2">
      <h3 className="text-lg font-semibold mb-2">System Snapshot</h3>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        {entries.map((e) => (
          <li key={e.label} className="flex justify-between">
            <span>{e.label}</span>
            <span className="font-mono">{e.value}</span>
          </li>
        ))}
      </ul>
      <div className="text-xs text-neutral-400 pt-2">
        Last Upload: {stats.last_upload || 'N/A'}<br />
        Last Manual Fix: {stats.last_manual_fix || 'N/A'}
      </div>
    </Card>
  );
}
