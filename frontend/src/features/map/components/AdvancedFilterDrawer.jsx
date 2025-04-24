// src/features/map/components/AdvancedFilterDrawer.jsx
import React from "react";
import Drawer from "@shared/components/ui/Drawer";
import PanelSection from "@shared/components/ui/PanelSection";
import { useSearch } from "@shared/context/SearchContext";

export default function AdvancedFilterDrawer() {
  const {
    filters,
    setFilters,
    isDrawerOpen,
    setIsDrawerOpen,
    clearAll,
  } = useSearch();

  const toggleGroupValue = (group, key) =>
    setFilters((prev) => ({
      ...prev,
      [group]: { ...prev[group], [key]: !prev[group][key] },
    }));

  const handleYearChange = (idx, value) =>
    setFilters((prev) => {
      const newRange = [...prev.yearRange];
      newRange[idx] = Number(value);
      return { ...prev, yearRange: newRange };
    });

  return (
    <Drawer
      open={isDrawerOpen}
      onClose={() => setIsDrawerOpen(false)}
      width="w-72"
      className="backdrop-blur-md"
    >
      <div
        className="
          flex flex-col h-full
          bg-[var(--surface)]/80 backdrop-blur-lg
          text-[var(--text)]
          p-4
          rounded-l-lg
        "
      >
        <header className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-display font-semibold">Filters</h2>
          <button
            onClick={clearAll}
            className="text-sm text-accent hover:underline"
          >
            Clear all
          </button>
        </header>

        <PanelSection title="Years">
          <div className="flex items-center space-x-2">
            <input
              type="number"
              value={filters.yearRange[0]}
              onChange={(e) => handleYearChange(0, e.target.value)}
              className="w-20 bg-[var(--surface)] border border-white/20 rounded p-1"
            />
            <span>—</span>
            <input
              type="number"
              value={filters.yearRange[1]}
              onChange={(e) => handleYearChange(1, e.target.value)}
              className="w-20 bg-[var(--surface)] border border-white/20 rounded p-1"
            />
          </div>
        </PanelSection>

        {[
          { label: "Event Types", key: "eventTypes" },
          { label: "Relations", key: "relations" },
          { label: "Sources", key: "sources" },
        ].map(({ label, key }) => (
          <PanelSection key={key} title={label}>
            <div className="flex flex-wrap gap-2">
              {Object.entries(filters[key]).map(([opt, val]) => (
                <button
                  key={opt}
                  onClick={() => toggleGroupValue(key, opt)}
                  className={`filter-pill ${
                    val ? "bg-accent text-black" : "bg-white/10 text-white"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </PanelSection>
        ))}

        <PanelSection title="Location Confidence">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.vague}
              onChange={() =>
                setFilters((prev) => ({ ...prev, vague: !prev.vague }))
              }
            />
            <span>Include vague / state-only places</span>
          </label>
        </PanelSection>

        <footer className="flex justify-end space-x-4 pt-4 border-t border-white/10 mt-6">
          <button
            onClick={() => setIsDrawerOpen(false)}
            className="px-4 py-2 bg-white text-black rounded hover:bg-neutral-200 transition"
          >
            Apply
          </button>
        </footer>
      </div>
    </Drawer>
  );
}
