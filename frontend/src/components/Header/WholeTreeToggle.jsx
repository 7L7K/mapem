import React from 'react';
import { useSearch } from '/context/SearchContext';

export default function WholeTreeToggle() {
  const { wholeTree, toggleWholeTree } = useSearch();

  return (
    <div className="flex flex-col">
      <label className="text-xs font-medium text-dim mb-1">
        Whole Tree View
      </label>
      <button
        onClick={toggleWholeTree}
        className={`px-4 py-2 text-sm rounded-md border transition-all ${
          wholeTree
            ? 'bg-accent text-black border-accent'
            : 'bg-surface text-white border-border hover:border-white/50'
        }`}
      >
        {wholeTree ? 'Showing All' : 'Focus Only'}
      </button>
    </div>
  );
}
