// src/features/map/components/PersonSelector.jsx
import React, { useState, useEffect } from 'react';
import { useMapControl } from '@shared/context/MapControlContext';
import { useSearch } from '@shared/context/SearchContext';
import * as api from '@lib/api/api';

export default function PersonSelector() {
  const { activeSection, toggleSection } = useMapControl();
  const { filters, setFilters } = useSearch();
  const open = activeSection === 'person';
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (filters.person.trim().length < 2) return setResults([]);
    api.searchPeople(filters.person).then(setResults);
  }, [filters.person]);

  const handleSelect = (person) => {
    setFilters((prev) => ({ ...prev, selectedPersonId: person.id }));
    toggleSection('person');
  };

  return (
    <div className={`transition-all ${open ? 'w-full' : 'w-40'} bg-[var(--surface)] border border-white/10 rounded overflow-hidden`}>  
      <ul className="divide-y divide-white/10">
        {results.map((p) => (
          <li key={p.id}>
            <button
              onClick={() => handleSelect(p)}
              className="w-full text-left px-3 py-2 hover:bg-white/10 transition"
            >
              {p.name} {p.birthYear && `(${p.birthYear})`}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
