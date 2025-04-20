// src/components/Filters/AdvancedFilterDrawer.jsx
import React from "react";
import Drawer from "../ui/Drawer";
import PanelSection from "../ui/PanelSection";

export default function AdvancedFilterDrawer({
  isOpen,
  onClose,
  filterState,
  setFilterState,
  onApply
}) {
  const toggle = (key, group) => {
    setFilterState((prev) => ({
      ...prev,
      [group]: {
        ...prev[group],
        [key]: !prev[group][key],
      },
    }));
  };

  return (
    <Drawer open={isOpen} onClose={onClose}>
      <div className="p-6 space-y-8 w-full max-w-md sm:w-80 h-full sm:h-auto bg-black/80 text-white backdrop-blur-md border-l border-white/10 overflow-auto">
        <h2 className="text-lg font-display font-semibold">Advanced Filters</h2>

        <PanelSection title="Event Types">
          {Object.keys(filterState.eventTypes).map((key) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filterState.eventTypes[key]}
                onChange={() => toggle(key, "eventTypes")}
              />
              {key}
            </label>
          ))}
        </PanelSection>

        <PanelSection title="Relations">
          {Object.keys(filterState.relations).map((key) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filterState.relations[key]}
                onChange={() => toggle(key, "relations")}
              />
              {key}
            </label>
          ))}
        </PanelSection>

        <PanelSection title="Sources">
          {Object.keys(filterState.sources).map((key) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filterState.sources[key]}
                onChange={() => toggle(key, "sources")}
              />
              {key}
            </label>
          ))}
        </PanelSection>

        <div className="flex justify-end mt-6">
          <button
            onClick={onApply}
            className="bg-white text-black px-4 py-2 rounded-md hover:bg-neutral-200 transition-all"
          >
            Apply
          </button>
        </div>
      </div>
    </Drawer>
  );
}
