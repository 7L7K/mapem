import React from "react";
import PropTypes from "prop-types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  PieChart, Pie, Cell, Legend, ResponsiveContainer
} from "recharts";

export default function AuditCharts({ stats, onFilter = () => {} }) {
  if (
    !stats ||
    !Array.isArray(stats.unresolved) ||
    typeof stats.sourceBreakdown !== "object"
  ) {
    return (
      <div className="text-center text-sm text-muted-foreground p-4">
        📊 Loading audit charts...
      </div>
    );
  }

  // backend gives { raw_name, count }
  const topUnresolved = stats.unresolved
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
    .map(i => ({ name: i.raw_name, value: i.count }));

  const sources = Object.entries(stats.sourceBreakdown).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="w-full h-64">
        <ResponsiveContainer>
          <BarChart data={topUnresolved} onClick={e => e && onFilter(e.activeLabel)}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis />
            <ReTooltip />
            <Bar dataKey="value" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="w-full h-64">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={sources}
              dataKey="value"
              nameKey="name"
              outerRadius={80}
              onClick={entry => entry && onFilter(entry.name)}
            >
              {sources.map((_, idx) => <Cell key={`cell-${idx}`} />)}
            </Pie>
            <Legend />
            <ReTooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

AuditCharts.propTypes = {
  stats: PropTypes.shape({
    unresolved:     PropTypes.arrayOf(
            PropTypes.shape({
        raw_name: PropTypes.string.isRequired,
        count:    PropTypes.number.isRequired,
      })
    ),
    sourceBreakdown: PropTypes.object,
  }),
  onFilter: PropTypes.func,
};
