
/* components/geocode/AuditCharts.jsx */
import React from 'react';
import PropTypes from 'prop-types';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  PieChart, Pie, Cell, Legend, ResponsiveContainer
} from 'recharts';

export default function AuditCharts({ stats, onFilter }) {
  const topUnresolved = stats.unresolved
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
    .map(item => ({ name: item.rawName, value: item.count }));
  const sources = Object.entries(stats.sourceBreakdown).map(([key, value]) => ({ name: key, value }));

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
            <Pie data={sources} dataKey="value" nameKey="name" outerRadius={80} onClick={(entry) => entry && onFilter(entry.name)}>
              {sources.map((entry, index) => (
                <Cell key={`cell-${index}`} />
              ))}
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
    unresolved: PropTypes.arrayOf(PropTypes.shape({ rawName: PropTypes.string, count: PropTypes.number })),
    sourceBreakdown: PropTypes.objectOf(PropTypes.number)
  }).isRequired,
  onFilter: PropTypes.func
};
AuditCharts.defaultProps = { onFilter: () => {} };
