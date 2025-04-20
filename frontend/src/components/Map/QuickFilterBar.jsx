import React from "react";

export default function QuickFilterBar({ filterState, setFilterState, onToggleDrawer }) {
  const handlePersonChange = (e) => {
    setFilterState((prev) => ({ ...prev, person: e.target.value }));
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col space-y-2">
        <label htmlFor="person-search" className="text-sm text-dim">
          Search Person:
        </label>
        <input
          type="text"
          id="person-search"
          placeholder="e.g. John..."
          value={filterState.person}
          onChange={handlePersonChange}
          className="px-3 py-2 rounded-md bg-background border border-border text-sm"
        />
      </div>

      <div>
        <button
          onClick={onToggleDrawer}
          className="mt-2 text-accent hover:underline text-sm"
        >
          ⚙️ Advanced Filters
        </button>
      </div>
    </div>
  );
}
