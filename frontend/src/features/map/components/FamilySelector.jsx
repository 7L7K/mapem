// src/features/map/components/FamilySelector.jsx
import React, { useState, useEffect } from 'react';
import { useMapControl } from '@shared/context/MapControlContext';
import { useSearch } from '@shared/context/SearchContext';
import * as api from '@lib/api/api';

export default function FamilySelector() {
  const { activeSection, toggleSection } = useMapControl();
  const { filters, setFilters } = useSearch();
  const open = activeSection === 'family';
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (filters.person.trim().length < 2) return setResults([]);
    api.search(filters.person).then(setResults);
  }, [filters.person]);

  const handleSelect = (family) => {
    setFilters((prev) => ({ ...prev, selectedFamilyId: family.id }));
    toggleSection('family');
  };

  return (
    <div className={`transition-all ${open ? 'w-full' : 'w-40'} bg-[var(--surface)] border border-white/10 rounded overflow-hidden`}>
      <ul className="divide-y divide-white/10">
        {results.map((f) => (
          <li key={f.id}>
            <button
              onClick={() => handleSelect(f)}
              className="w-full text-left px-3 py-2 hover:bg-white/10 transition"
            >
              {f.name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
