// src/shared/components/DebugStatusBadge.jsx
import React from 'react';
import { useTree } from '@shared/context/TreeContext';
import { useSearch } from '@shared/context/SearchContext';

export default function DebugStatusBadge() {
  const { treeId } = useTree();
  const { filters } = useSearch();

  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white text-xs px-3 py-2 rounded shadow-lg z-[9999]">
      <div>🌳 Tree: {treeId || 'None'}</div>
      <div>🔎 Filters: {Object.keys(filters).length}</div>
    </div>
  );
}
