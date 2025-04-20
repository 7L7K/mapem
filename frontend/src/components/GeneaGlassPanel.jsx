// src/components/GeneaGlassPanel.jsx
import React, { useRef, useEffect, useState } from 'react';

export default function GeneaGlassPanel({ filterState, setFilterState, onOpenAdvanced }) {
  const panelRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 20 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      setPosition((prev) => ({
        x: prev.x + e.movementX,
        y: prev.y + e.movementY,
      }));
    };
    const stopDragging = () => setIsDragging(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', stopDragging);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', stopDragging);
    };
  }, [isDragging]);

  const toggleFilter = (key, group) => {
    setFilterState((s) => ({
      ...s,
      [group]: { ...s[group], [key]: !s[group][key] },
    }));
  };

  return (
    <aside
      ref={panelRef}
      className="absolute z-50 w-80 rounded-2xl p-4 cursor-move text-white"
      style={{
        top: `${position.y}px`,
        left: `${position.x}px`,
        backgroundColor: 'rgba(20, 20, 20, 0.5)',
        backdropFilter: 'blur(10px) brightness(0.6)',
        border: '1px solid rgba(255,255,255,0.15)',
        boxShadow: '0 4px 30px rgba(0,0,0,0.5)',
      }}
      onMouseDown={(e) => {
        if (e.target === panelRef.current) setIsDragging(true);
      }}
    >
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold tracking-wide">🔍 Filters</h2>
        <button onClick={onOpenAdvanced} className="text-sm text-blue-300 hover:underline">
          ⚙️ Advanced
        </button>
      </div>

      <div className="space-y-5">
        <div>
          <label className="text-xs uppercase opacity-60">Search Person</label>
          <input
            type="text"
            className="w-full mt-1 px-3 py-2 bg-white/10 border border-white/20 rounded text-sm placeholder-white/50 text-white focus:outline-none"
            placeholder="Type name..."
            value={filterState.person}
            onChange={(e) =>
              setFilterState((s) => ({ ...s, person: e.target.value }))
            }
          />
        </div>

        <div>
          <label className="text-xs uppercase opacity-60 mb-1 block">Event Types</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(filterState.eventTypes).map(([key, val]) => (
              <button
                key={key}
                onClick={() => toggleFilter(key, 'eventTypes')}
                className={`px-3 py-1 text-sm rounded-full border transition backdrop-blur ${
                    val
                      ? 'bg-white/20 border-white/30 font-semibold text-white'
                      : 'bg-white/10 border-white/20 text-white/80'
                  }`}
                                >
                {key}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs uppercase opacity-60 mb-1 block">Sources</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(filterState.sources).map(([key, val]) => (
              <button
                key={key}
                onClick={() => toggleFilter(key, 'sources')}
                className={`px-3 py-1 text-sm rounded-full border transition backdrop-blur ${
                    val
                      ? 'bg-white/20 border-white/30 font-semibold text-white'
                      : 'bg-white/10 border-white/20 text-white/80'
                  }`}
                                >
                {key}
              </button>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
