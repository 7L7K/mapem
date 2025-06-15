import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { Card, CardContent } from "@shared/components/ui/Card";
import Spinner from "@shared/components/ui/Spinner";
import Tooltip from "@shared/components/ui/Tooltip";
import { formatDateWithTime } from "@shared/utils/formatters";
import ErrorBoundary from "@shared/components/ErrorBoundary";
import useFetch from "@shared/hooks/useFetch";
import Sparkline from "@shared/components/ui/Sparkline";
import { devLog } from "@shared/utils/devLogger";

// Metrics definition for cards
const METRICS = [
  { key: "total", label: "Total", tooltip: "Total locations processed" },
  { key: "resolved", label: "Resolved", tooltip: "Successfully geocoded" },
  { key: "unresolved", label: "Unresolved", tooltip: "Failed or vague locations" },
  { key: "manual", label: "Manual Overrides", tooltip: "Fixed manually" },
  { key: "failed", label: "Failed", tooltip: "API or system errors" },
];

function StatsPanelInner({
  stats = {},
  loading = false,
  lastUpload = null,
}) {
  useEffect(() => {
    devLog("StatsPanel", "🔄 Render stats", JSON.stringify({ stats, loading, lastUpload }));
  }, [stats, loading, lastUpload]);

  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4"
      role="region"
      aria-label="Geocode statistics"
      tabIndex={0}
    >
      {METRICS.map(({ key, label, tooltip }) => {
        let value = loading ? null : stats[key] ?? 0;
        // If backend sends null/undefined/NaN or bogus value, clean it
        value = value === null || value === undefined || isNaN(value) ? "—" : value;

        let delta = stats[`${key}Change`];
        delta = delta === null || delta === undefined || isNaN(delta) ? null : delta;

        const isPositive = delta !== null && delta >= 0;
        const sparkData = stats[`${key}History`] ?? [];
        return (
          <Card
            key={key}
            className="relative hover:scale-105 transition-transform focus-within:ring-2"
            aria-labelledby={`stat-${key}-label`}
          >
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
                    <h3
                      id={`stat-${key}-label`}
                      className="text-sm uppercase text-gray-500"
                    >
                      {label}
                    </h3>
                  </Tooltip>
                  <p className="text-2xl font-bold" aria-live="polite">
                    {typeof value === "number" ? value.toLocaleString() : value}
                  </p>
                  <span
                    className={`mt-1 text-sm font-medium ${
                      delta == null
                        ? "text-gray-400"
                        : isPositive
                        ? "text-green-500"
                        : "text-red-500"
                    }`}
                    aria-label={
                      delta == null
                        ? "No change"
                        : `${isPositive ? "Increase" : "Decrease"} of ${Math.abs(delta)}%`
                    }
                  >
                    {delta == null
                      ? "—"
                      : `${isPositive ? "+" : ""}${delta}%`}
                  </span>
                  {sparkData.length > 0 && (
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
  stats: PropTypes.object,
  loading: PropTypes.bool,
  lastUpload: PropTypes.oneOfType([PropTypes.instanceOf(Date), PropTypes.string]),
};

export default function StatsPanel({ apiEndpoint }) {
  const { data: apiData, loading, error, refetch } = useFetch(
    apiEndpoint,
    {},
    { verbose: window.DEBUG_FETCH }
  );

  // PATCH: Support for shape { data, error }
  const stats = apiData?.data || {};
  const lastUpload = stats.lastUpload || null;

  if (error || apiData?.error) {
    devLog("StatsPanel", "❌ Fetch error", error || apiData?.error, { stats, apiData });
    return <div className="text-red-500">Failed to load stats.</div>;
  }

  return (
    <ErrorBoundary fallback={<div className="text-red-500">Stats unavailable.</div>}>
      <div className="flex justify-end mb-2">
        <button
          onClick={refetch}
          className="underline text-sm flex items-center gap-1"
          disabled={loading}
          aria-disabled={loading}
        >
          {loading ? (
            <span className="mr-1"><Spinner size={16} /></span>
          ) : null}
          Refresh
        </button>
      </div>
      <StatsPanelInner stats={stats} loading={loading} lastUpload={lastUpload} />
    </ErrorBoundary>
  );
}

StatsPanel.propTypes = {
  apiEndpoint: PropTypes.string.isRequired,
};
