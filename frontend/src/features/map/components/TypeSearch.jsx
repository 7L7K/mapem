// src/features/map/components/TypeSearch.jsx
import React from 'react';
import { useMapControl } from '@shared/context/MapControlContext';
import { useSearch } from '@shared/context/SearchContext';

export default function TypeSearch() {
  const { activeSection, toggleSection } = useMapControl();
  const { filters, setFilters } = useSearch();
  const open = activeSection === 'search';

  const onFocus = () => toggleSection('search');
  const onBlur = () => {}; // keep open until selection

  const handleChange = (e) => setFilters((f) => ({ ...f, person: e.target.value }));

  return (
    <div className={`transition-all ${open ? 'w-full' : 'w-40'}`}>
      <input
        className="bg-surface border border-border rounded px-3 py-1 w-full"
        placeholder="Type name..."
        value={filters.person}
        onFocus={onFocus}
        onChange={handleChange}
      />
      {/* TODO: render autocomplete dropdown here when open */}
    </div>
  );
}
