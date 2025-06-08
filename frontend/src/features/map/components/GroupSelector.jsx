// src/features/map/components/GroupSelector.jsx
import React, { useState, useEffect } from 'react';
import { useMapControl } from '@shared/context/MapControlContext';
import { useSearch } from '@shared/context/SearchContext';
import * as api from '@lib/api/api';

export default function GroupSelector() {
  const { activeSection, toggleSection } = useMapControl();
  const { filters, setFilters } = useSearch();
  const open = activeSection === 'compare';
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (filters.person.trim().length < 2) return setResults([]);
    api.search(filters.person).then(setResults);
  }, [filters.person]);

  const toggleId = (id) => {
    setFilters((prev) => {
      const exists = prev.compareIds.includes(id);
      const compareIds = exists
        ? prev.compareIds.filter((v) => v !== id)
        : [...prev.compareIds, id];
      return { ...prev, compareIds };
    });
  };

  const done = () => toggleSection('compare');

  return (
    <div className={`transition-all ${open ? 'w-full' : 'w-40'} bg-[var(--surface)] border border-white/10 rounded overflow-hidden`}>
      <ul className="divide-y divide-white/10 max-h-60 overflow-y-auto">
        {results.map((p) => (
          <li key={p.id} className="flex items-center">
            <label className="flex-1 px-3 py-2 hover:bg-white/10">
              <input
                type="checkbox"
                checked={filters.compareIds.includes(p.id)}
                onChange={() => toggleId(p.id)}
                className="mr-2"
              />
              {p.name}
            </label>
          </li>
        ))}
      </ul>
      <button
        onClick={done}
        className="w-full bg-accent/20 hover:bg-accent/40 rounded-lg py-1 text-sm mt-2 transition text-white"
      >
        Done
      </button>
    </div>
  );
}
