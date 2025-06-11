import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Card from '@shared/components/ui/card';
import CardContent from '@shared/components/ui/card';

import  Spinner  from '@shared/components/ui/spinner';
import  Tooltip  from '@shared/components/ui/tooltip';
import  formatDateWithTime  from '@shared/utils/formatters';
import ErrorBoundary from '@shared/components/ErrorBoundary';
import useFetch from '@shared/hooks/useFetch';
import Sparkline from '@shared/components/ui/sparkline';

const METRICS = [
  { key: 'total', label: 'Total', tooltip: 'Total locations processed' },
  { key: 'resolved', label: 'Resolved', tooltip: 'Successfully geocoded' },
  { key: 'unresolved', label: 'Unresolved', tooltip: 'Failed or vague locations' },
  { key: 'manual', label: 'Manual Overrides', tooltip: 'Fixed manually' },
  { key: 'failed', label: 'Failed', tooltip: 'API or system errors' },
];

function StatsPanelInner({ stats, loading, lastUpload }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" role="region" aria-label="Geocode statistics">
      {METRICS.map(({ key, label, tooltip }) => {
        const value = stats[key] ?? 0;
        const delta = stats[`${key}Change`] || 0;
        const isPositive = delta >= 0;
        const sparkData = stats[`${key}History`] || []; // array of nums
        return (
          <Card key={key} className="relative" aria-labelledby={`stat-${key}-label`}>
            <CardContent className="flex flex-col items-center p-4">
              {loading ? (
                <div className="w-full animate-pulse space-y-2">
                  <div className="h-4 bg-gray-300 rounded"></div>
                  <div className="h-8 bg-gray-300 rounded"></div>
                  <div className="h-4 bg-gray-300 rounded"></div>
                </div>
              ) : (
                <>
                  <Tooltip content={tooltip}>
                    <h3 id={`stat-${key}-label`} className="text-sm uppercase text-gray-500">
                      {label}
                    </h3>
                  </Tooltip>
                  <p className="text-2xl font-bold" aria-live="polite">
                    {value.toLocaleString()}
                  </p>
                  <span
                    className={`mt-1 text-sm font-medium ${isPositive ? 'text-green-500' : 'text-red-500'}`}
                    aria-label={`${delta >= 0 ? 'Increase' : 'Decrease'} of ${Math.abs(delta)} percent`}
                  >
                    {isPositive ? '+' : ''}{delta}%
                  </span>
                  {!!sparkData.length && (
                    <div className="w-full mt-2 h-6">
                      <Sparkline data={sparkData} />
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        );
      })}

      {!loading && lastUpload && (
        <div className="col-span-full text-center text-gray-400 text-sm mt-2">
          Last upload: {formatDateWithTime(lastUpload)}
        </div>
      )}
    </div>
  );
}

StatsPanelInner.propTypes = {
  stats: PropTypes.object.isRequired,
  loading: PropTypes.bool,
  lastUpload: PropTypes.oneOfType([PropTypes.instanceOf(Date), PropTypes.string]),
};

StatsPanelInner.defaultProps = {
  loading: false,
  lastUpload: null,
};

export default function StatsPanel({ apiEndpoint }) {
  // useFetch is a custom hook that returns { data, loading, error, refresh }
  const { data: stats, loading, error, refresh } = useFetch(apiEndpoint, { pollingInterval: 60000 });
  
  if (error) return <div className="text-red-500">Failed to load stats.</div>;

  return (
    <ErrorBoundary fallback={<div className="text-red-500">Stats unavailable.</div>}>
      <div className="flex justify-end mb-2">
        <button onClick={refresh} className="underline text-sm">Refresh</button>
      </div>
      <StatsPanelInner stats={stats || {}} loading={loading} lastUpload={stats?.lastUpload} />
    </ErrorBoundary>
  );
}

StatsPanel.propTypes = {
  apiEndpoint: PropTypes.string.isRequired,
};
