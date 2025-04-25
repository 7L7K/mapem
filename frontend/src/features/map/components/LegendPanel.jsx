// src/features/map/components/LegendPanel.jsx
import React, { useState, useEffect } from 'react';
import { useLegend } from '@shared/context/LegendContext';
import { useSearch } from '@shared/context/SearchContext';
import RelativesPopover from './RelativesPopover';
import { devLog } from '@shared/utils/devLogger';

export default function LegendPanel() {
  const { counts } = useLegend();
  const { filters } = useSearch();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    devLog('LegendPanel', '🔄 render', { counts, filters });
  }, [counts, filters]);

  return (
    <div
      className="legend-panel fixed left-4 bottom-4 z-40 rounded-2xl p-4 text-sm space-y-3 shadow-xl backdrop-blur-md"
      style={{
        width: '288px',                // override w-72 (18rem)
        backgroundColor: 'rgba(24,24,24,0.85)',
        maxHeight: 'none',            // ensure it's not capped
        bottom: '1rem'                // override negative positioning if it happens
      }}
    >
      <h3 className="font-semibold mb-1 text-white">Legend</h3>

      {[
        ['👤', 'People', counts.people],
        ['👪', 'Families', counts.families],
        filters.selectedPersonId && ['🏠', 'Household', counts.household],
        ['🌳', 'Whole Tree', counts.wholeTree],
      ]
        .filter(Boolean)
        .map(([icon, label, value]) => (
          <div key={label} className="flex justify-between text-white">
            <div className="flex items-center">
              <span className="mr-2">{icon}</span>
              {label}
            </div>
            <div>{value}</div>
          </div>
        ))}

      <button
        onClick={() => setOpen(!open)}
        className="w-full bg-accent/20 hover:bg-accent/40 rounded-lg py-1 text-sm transition text-white"
      >
        Choose Relatives
      </button>

      {open && <RelativesPopover onClose={() => setOpen(false)} />}
    </div>
  );
}
