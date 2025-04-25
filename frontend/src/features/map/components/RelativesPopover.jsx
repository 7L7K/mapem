// src/features/map/components/RelativesPopover.jsx
import React from 'react';
import { useLegend } from '@shared/context/LegendContext';
import { useSearch } from '@shared/context/SearchContext';

export default function RelativesPopover({ onClose }) {
  const { counts } = useLegend();
  const { filters, setFilters } = useSearch();
  const relations = counts.relatives || {};
  const toggle = (key) => setFilters((f) => ({ ...f, relations: { ...f.relations, [key]: !f.relations[key] } }));

  return (
    <div className="absolute left-full ml-2 top-0 bg-[rgba(24,24,24,0.95)] backdrop-blur-md rounded-xl p-3 space-y-2 shadow-xl z-50 w-44">
      {Object.entries(relations).map(([k, list]) => (
        <button key={k} onClick={() => toggle(k)} className="flex justify-between w-full text-left px-2 py-1 rounded hover:bg-white/10">
          <span className="capitalize">{k}</span>
          <span>{list.length}</span>
        </button>
      ))}
      <button onClick={onClose} className="mt-2 w-full py-1 bg-accent/20 hover:bg-accent/40 rounded text-sm">Close</button>
    </div>
  );
}
