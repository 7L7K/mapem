// src/features/map/components/LegendPanel.jsx
import React, { useState, useEffect } from 'react';
import { Card } from '@shared/components/ui/Card';
import { useLegend } from '@shared/context/LegendContext';
import { useSearch } from '@shared/context/SearchContext';
import RelativesPopover from './RelativesPopover';
import { devLog } from '@shared/utils/devLogger';

export default function LegendPanel() {
  const { counts } = useLegend();
  const { filters, mode } = useSearch();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    devLog('LegendPanel', '🔄 render', { counts, filters });
  }, [counts, filters]);

  return (
    <Card
      className="legend-panel fixed left-4 bottom-4 z-40 rounded-2xl p-4 text-sm space-y-3 shadow-xl backdrop-blur-md w-72"
      style={{ backgroundColor: 'rgba(24,24,24,0.85)' }}
    >
      <h3 className="font-semibold mb-1 text-white">Legend</h3>

      {(() => {
        const items = [];
        if (mode === 'person' || mode === 'compare')
          items.push(['👤', 'People', counts.people]);
        if (mode === 'family')
          items.push(['👪', 'Families', counts.families]);
        if (mode === 'person' && filters.selectedPersonId) {
          items.push(['🏠', 'Household', counts.household]);
        }

        items.push(['🌳', 'Whole Tree', counts.wholeTree]);
        return items;
      })()
        .map(([icon, label, value]) => (
          <div key={label} className="flex justify-between text-white">
            <div className="flex items-center">
              <span className="mr-2">{icon}</span>
              {label}
            </div>
            <div>{value}</div>
          </div>
        ))}

      <div className="h-px bg-white/10 my-1" />
      <div className="space-y-1 text-white/80">
        <div className="flex items-center gap-2"><span className="inline-block w-4 h-[2px] bg-[#4fb4ff]" /> Movement</div>
        <div className="flex items-center gap-2"><span className="inline-block w-4 h-[2px] bg-[#ff4d4f]" /> Suspicious speed</div>
        <div className="flex items-center gap-2"><span className="inline-block w-4 h-[2px] bg-[#9aa0a6]" /> Impossible</div>
        <div className="flex items-center gap-2"><span className="inline-block w-3 h-3 bg-[#888] rounded-sm" /> Historical border</div>
      </div>

      <button
        onClick={() => setOpen(!open)}
        className="w-full bg-accent/20 hover:bg-accent/40 rounded-lg py-1 text-sm transition text-white"
      >
        Choose Relatives
      </button>

      {open && <RelativesPopover onClose={() => setOpen(false)} />}
    </Card>
  );
}
