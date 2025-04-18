import React from "react";

const AdvancedFilterDrawer = ({ filterState, setFilterState, isOpen, onClose, onApply }) => {
  if (!isOpen) return null;

  const toggleRelation = (key) => {
    console.log(`🔁 Toggling relation: ${key}`);
    setFilterState(prev => ({
      ...prev,
      relations: {
        ...prev.relations,
        [key]: !prev.relations[key]
      }
    }));
  };

  const toggleSource = (key) => {
    console.log(`🛰️ Toggling source: ${key}`);
    setFilterState(prev => ({
      ...prev,
      sources: {
        ...prev.sources,
        [key]: !prev.sources[key]
      }
    }));
  };

  const toggleEventType = (key) => {
    console.log(`📍 Toggling eventType: ${key}`);
    setFilterState(prev => ({
      ...prev,
      eventTypes: {
        ...prev.eventTypes,
        [key]: !prev.eventTypes[key]
      }
    }));
  };

  const resetFilters = () => {
    console.log("🔄 Resetting filters to default");
    setFilterState(prev => ({
      ...prev,
      eventTypes: { birth: true, death: true, residence: true },
      relations: { direct: true, siblings: false, cousins: false, inlaws: false },
      sources: { gedcom: true, census: true, manual: false, ai: false }
    }));
  };

  const safe = (key, defaultVal = false) =>
    filterState?.[key] || defaultVal;

  return (
    <div className="fixed top-12 right-0 w-80 h-full bg-neutral-900 text-white shadow-lg z-40 p-4 overflow-y-auto border-l border-neutral-800">
      <h2 className="text-lg font-semibold mb-3">Advanced Filters</h2>

      {/* Event Types */}
      <div className="mb-4">
        <p className="font-medium mb-1">Event Types</p>
        {['birth', 'death', 'residence'].map(type => (
          <label key={type} className="block text-sm mb-1">
            <input
              type="checkbox"
              checked={filterState?.eventTypes?.[type] || false}
              onChange={() => toggleEventType(type)}
              className="mr-2"
            />
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </label>
        ))}
      </div>

      {/* Relation Types */}
      <div className="mb-4">
        <p className="font-medium mb-1">Relation Types</p>
        {Object.entries(filterState?.relations || {}).map(([key, value]) => (
          <label key={key} className="block text-sm mb-1">
            <input
              type="checkbox"
              checked={value}
              onChange={() => toggleRelation(key)}
              className="mr-2"
            />
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </label>
        ))}
      </div>

      {/* Event Sources */}
      <div className="mb-4">
        <p className="font-medium mb-1">Event Sources</p>
        {Object.entries(filterState?.sources || {}).map(([key, value]) => (
          <label key={key} className="block text-sm mb-1">
            <input
              type="checkbox"
              checked={value}
              onChange={() => toggleSource(key)}
              className="mr-2"
            />
            {key.toUpperCase()}
          </label>
        ))}
      </div>

      <div className="flex gap-2 justify-end mt-6">
        <button
          className="bg-neutral-700 hover:bg-neutral-600 px-3 py-1 rounded text-sm"
          onClick={onClose}
        >
          Cancel
        </button>
        <button
          className="bg-emerald-600 hover:bg-emerald-700 px-3 py-1 rounded text-sm"
          onClick={() => {
            console.log("✅ Apply filters clicked");
            onApply();
          }}
        >
          Apply
        </button>
        <button
          className="bg-neutral-700 hover:bg-neutral-600 px-3 py-1 rounded text-sm"
          onClick={resetFilters}
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default AdvancedFilterDrawer;
