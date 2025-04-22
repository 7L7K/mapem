import React from 'react';
import { useSearch } from '/context/SearchContext';

export default function FilterDrawer() {
  const {
    showFilters,
    toggleFilters,
    filterState,
    setFilterState,
  } = useSearch();

  const toggleEventType = (type) => {
    setFilterState((prev) => ({
      ...prev,
      eventTypes: {
        ...prev.eventTypes,
        [type]: !prev.eventTypes[type],
      },
    }));
  };

  return showFilters ? (
    <aside className="fixed top-0 right-0 h-full w-80 bg-[#101010]/90 backdrop-blur-lg text-white z-50 shadow-lg transition-transform duration-300 translate-x-0">
      <button onClick={toggleFilters} className="absolute top-4 right-4 text-xl">✕</button>
      <div className="p-6 pt-14 space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">Event Types</h3>
          {Object.entries(filterState.eventTypes).map(([key, value]) => (
            <label key={key} className="block text-sm">
              <input
                type="checkbox"
                checked={value}
                onChange={() => toggleEventType(key)}
                className="mr-2"
              />
              {key}
            </label>
          ))}
        </div>
        {/* Future sections go here */}
      </div>
    </aside>
  ) : null;
}
