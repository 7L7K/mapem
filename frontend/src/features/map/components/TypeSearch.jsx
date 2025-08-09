// src/features/map/components/TypeSearch.jsx
import React, { useState } from 'react';
import { useMapControl } from '@shared/context/MapControlContext';
import { useSearch } from '@shared/context/SearchContext';
import { useTree } from '@shared/context/TreeContext';
import { searchPeopleByName } from '@features/people/api/search';

export default function TypeSearch() {
  const { activeSection, toggleSection } = useMapControl();
  const { filters, setFilters } = useSearch();
  const { treeId } = useTree();
  const [suggestions, setSuggestions] = useState([]);
  const [local, setLocal] = useState(filters.person || '');
  const open = activeSection === 'search';

  const onFocus = () => toggleSection('search');
  const onBlur = () => { }; // keep open until selection

  const handleChange = async (e) => {
    const v = e.target.value;
    setLocal(v);
    setFilters((f) => ({ ...f, person: v }));
    if (v && treeId) {
      try {
        const res = await searchPeopleByName(treeId, v);
        setSuggestions(res);
      } catch { }
    } else {
      setSuggestions([]);
    }
  };

  return (
    <div className={`transition-all ${open ? 'w-full' : 'w-40'}`}>
      <input
        className="bg-surface border border-border rounded px-3 py-1 w-full"
        placeholder="Type name..."
        value={local}
        onFocus={onFocus}
        onChange={handleChange}
      />
      {open && suggestions.length > 0 && (
        <div className="mt-1 bg-black/80 text-white text-xs rounded-md border border-white/10 max-h-64 overflow-auto">
          {suggestions.map(p => (
            <button
              key={p.id}
              className="w-full text-left px-3 py-1 hover:bg-white/10"
              onMouseDown={() => { setFilters({ person: p.id }); setLocal(p.name); setSuggestions([]); }}
            >{p.name}</button>
          ))}
        </div>
      )}
    </div>
  );
}
