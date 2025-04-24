import React from 'react';
import { useSearch } from '@shared/context/SearchContext'
const modes = [
  { value: 'person', label: '👤 Person' },
  { value: 'family', label: '🏡 Family' },
  { value: 'compare', label: '⚔️ Compare' },
];

export default function ModeSelector() {
  const { mode, setMode } = useSearch();

  return (
    <div className="flex flex-col">
      <label className="text-xs font-medium text-dim mb-1">Mode</label>
      <div className="flex gap-2">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => setMode(m.value)}
            className={`px-3 py-2 rounded-md text-sm border ${
              mode === m.value
                ? 'bg-accent text-black border-accent'
                : 'bg-surface text-white border-border hover:border-white/50'
            } transition-all`}
          >
            {m.label}
          </button>
        ))}
      </div>
    </div>
  );
}
