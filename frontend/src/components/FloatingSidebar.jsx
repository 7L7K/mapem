// src/components/FloatingSidebar.jsx
import React, { useState } from 'react';

export default function FloatingSidebar({
  filterState,
  onPersonChange,
  onToggleFilters,
  onSelectPerson,
  movements
}) {
  const [suggestions, setSuggestions] = useState([]);

  const handleChange = (e) => {
    const value = e.target.value;
    onPersonChange(value);
    if (value.length > 0) {
      const uniqueNames = Array.from(new Set(movements.map((m) => m.person_name)));
      setSuggestions(uniqueNames.filter((name) =>
        name.toLowerCase().includes(value.toLowerCase())
      ));
    } else {
      setSuggestions([]);
    }
  };

  return (
    <>
      {/* Desktop panel */}
      <div className="hidden sm:block fixed top-20 left-6 w-72 p-4 rounded-2xl shadow-xl z-50 backdrop-blur-md bg-black/70 border border-white/10">
        <input
          type="text"
          value={filterState.person}
          onChange={handleChange}
          placeholder="Search Person..."
          className="w-full px-4 py-2 rounded-xl bg-white text-black shadow-inner"
        />
        {suggestions.length > 0 && (
          <div className="mt-2 max-h-60 overflow-y-auto rounded-md border border-white/10 bg-black/80 backdrop-blur-md shadow-lg text-white">
            {suggestions.slice(0, 8).map((name) => (
              <div
                key={name}
                onClick={() =>
                  onSelectPerson({
                    person_id: movements.find((m) => m.person_name === name)?.person_id,
                    person_name: name
                  })
                }
                className="px-3 py-2 hover:bg-white/10 cursor-pointer text-sm"
              >
                {name}
              </div>
            ))}
          </div>
        )}
        <button
          onClick={onToggleFilters}
          className="mt-4 w-full border border-white/20 text-white rounded-md px-3 py-2 hover:bg-white hover:text-black transition-all"
        >
          ⚙️ Advanced Filters
        </button>
      </div>

      {/* Mobile bottom sheet */}
      <div className="sm:hidden fixed bottom-0 inset-x-0 p-4 bg-black/80 backdrop-blur-md text-white rounded-t-2xl shadow-lg z-50 max-h-[50vh] overflow-auto">
        <div className="relative">
          <input
            type="text"
            value={filterState.person}
            onChange={handleChange}
            placeholder="Search Person..."
            className="w-full px-4 py-2 rounded-xl bg-white text-black shadow-inner"
          />
          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 w-full mt-2 max-h-40 overflow-y-auto rounded-md border border-white/10 bg-black/80 backdrop-blur-md shadow-lg text-white">
              {suggestions.slice(0, 6).map((name) => (
                <div
                  key={name}
                  onClick={() =>
                    onSelectPerson({
                      person_id: movements.find((m) => m.person_name === name)?.person_id,
                      person_name: name
                    })
                  }
                  className="px-3 py-2 hover:bg-white/10 cursor-pointer text-sm"
                >
                  {name}
                </div>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={onToggleFilters}
          className="mt-4 w-full border border-white/20 text-white rounded-md px-3 py-2 hover:bg-white hover:text-black transition-all"
        >
          ⚙️ Advanced Filters
        </button>
      </div>
    </>
  );
}
