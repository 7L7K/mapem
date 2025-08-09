// src/shared/components/DebugStatusBadge.jsx
import React from 'react';
import { useTree } from '@shared/context/TreeContext';
import { useSearch } from '@shared/context/SearchContext';

export default function DebugStatusBadge() {
  const { treeId } = useTree();
  const { filters } = useSearch();
  const isDev = import.meta.env.DEV;
  const [online, setOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);

  if (!isDev) return null;
  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white text-xs px-3 py-2 rounded shadow-lg z-[9999] flex items-center gap-3">
      <div>🌳 Tree: {treeId || 'None'}</div>
      <div>🔎 Filters: {Object.keys(filters).length}</div>
      <div className={online ? 'text-green-400' : 'text-red-400'}>{online ? 'online' : 'offline'}</div>
    </div>
  );
}
