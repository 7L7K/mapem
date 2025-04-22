import React from 'react';
import { useSearch } from '/context/SearchContext';

const eventOptions = [
  { key: 'birth', label: 'Birth', icon: '👶' },
  { key: 'residence', label: 'Residence', icon: '🏠' },
  { key: 'death', label: 'Death', icon: '⚰️' },
];

const relationOptions = [
  { key: 'direct', label: 'Direct', icon: '🧬' },
  { key: 'siblings', label: 'Siblings', icon: '👫' },
  { key: 'cousins', label: 'Cousins', icon: '👪' },
  { key: 'inlaws', label: 'In-laws', icon: '🤝' },
];

export default function FilterDropdown() {
  const {
    showFilters,
    filterState,
    setFilterState,
  } = useSearch();

  if (!showFilters) return null;

  const toggleField = (group, key) => {
    setFilterState(prev => ({
      ...prev,
      [group]: {
        ...prev[group],
        ...(key ? { [key]: !prev[group][key] } : { vague: !prev.vague }),
      },
    }));
  };

  return (
    <div className="absolute top-full left-0 mt-1 w-64 bg-black/90 backdrop-blur-md text-white border border-white/15 rounded-lg shadow-lg p-4 z-50">
      <div className="mb-4">
        <h4 className="font-semibold mb-2">Event Types</h4>
        {eventOptions.map(o => (
          <label key={o.key} className="flex items-center gap-2 text-sm mb-1">
            <input
              type="checkbox"
              checked={filterState.eventTypes[o.key]}
              onChange={() => toggleField('eventTypes', o.key)}
            />
            <span>{o.icon} {o.label}</span>
          </label>
        ))}
      </div>

      <div className="mb-4">
        <h4 className="font-semibold mb-2">Year Range</h4>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={filterState.year[0]}
            onChange={(e) =>
              setFilterState(p => ({ ...p, year: [Number(e.target.value), p.year[1]] }))
            }
            className="w-16 p-1 bg-gray-900 rounded text-sm text-white"
          />
          <span>–</span>
          <input
            type="number"
            value={filterState.year[1]}
            onChange={(e) =>
              setFilterState(p => ({ ...p, year: [p.year[0], Number(e.target.value)] }))
            }
            className="w-16 p-1 bg-gray-900 rounded text-sm text-white"
          />
        </div>
      </div>

      <div className="mb-4">
        <h4 className="font-semibold mb-2">Relations</h4>
        {relationOptions.map(o => (
          <label key={o.key} className="flex items-center gap-2 text-sm mb-1">
            <input
              type="checkbox"
              checked={filterState.relations[o.key]}
              onChange={() => toggleField('relations', o.key)}
            />
            <span>{o.icon} {o.label}</span>
          </label>
        ))}
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={filterState.vague}
          onChange={() => toggleField()}
        />
        <span>Include vague locations</span>
      </label>
    </div>
  );
}
