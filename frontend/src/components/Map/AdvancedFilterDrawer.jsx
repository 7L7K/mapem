import React from "react";
import Drawer from "../ui/Drawer";
import PanelSection from "../ui/PanelSection";
import { useSearch } from "/context/SearchContext";

export default function AdvancedFilterDrawer({ isOpen, onClose, onApply }) {
  const { filters, toggleFilter } = useSearch();

  return (
    <Drawer open={isOpen} onClose={onClose}>
      <div className="p-6 space-y-8 w-full max-w-md sm:w-80 h-full sm:h-auto bg-black/80 text-white backdrop-blur-md border-l border-white/10 overflow-auto">
        <h2 className="text-lg font-display font-semibold">Advanced Filters</h2>

        {["eventTypes", "relations", "sources"].map((group) => (
          <PanelSection key={group} title={group}>
            {Object.keys(filters[group] || {}).map((key) => (
              <label key={key} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters[group][key]}
                  onChange={() => toggleFilter(group, key)}
                />
                {key}
              </label>
            ))}
          </PanelSection>
        ))}

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
