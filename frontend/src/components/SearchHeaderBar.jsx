import React, { useEffect, useState, useRef } from 'react';
import { useSearch } from '/context/SearchContext';
import FilterDropdown from './FilterDropdown';

export default function SearchHeaderBar() {
  const {
    searchText, setSearchText, setSelectedPerson,
    mode, setMode, toggleFilters, getActiveFilterCount
  } = useSearch();

  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef();
  const [showMode, setShowMode] = useState(false);

  useEffect(() => {
    if (!searchText) return setSuggestions([]);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/people?q=${encodeURIComponent(searchText)}`);
        setSuggestions(await res.json());
      } catch { setSuggestions([]); }
      setLoading(false);
    }, 300);
  }, [searchText]);

  return (
    <div className="relative flex items-center gap-2 bg-white/10 backdrop-blur-md shadow-lg rounded-full px-4 py-2 text-white z-40 ring-1 ring-white/10">
      <input
        type="text"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        placeholder="Search person…"
        className="bg-transparent outline-none placeholder-white/60 text-sm pl-2 pr-4 w-40"
      />

      <div className="relative">
        <button onClick={() => setShowMode(v => !v)} className="px-2 py-1 bg-white/20 hover:bg-white/30 rounded text-sm capitalize">
          {mode} ▾
        </button>
        {showMode && (
          <ul className="absolute bg-black/90 rounded shadow">
            {['person', 'family', 'group'].map(m => (
              <li key={m} onClick={() => { setMode(m); setShowMode(false); }} className={`px-3 py-1 hover:bg-white/10 ${m === mode && 'font-semibold'}`}>
                {m}
              </li>
            ))}
          </ul>
        )}
      </div>

      <button
        onClick={toggleFilters}
        className="px-2 py-1 bg-white/20 hover:bg-white/30 rounded text-sm"
      >
        Filters ({getActiveFilterCount()}) ▾
      </button>
      <FilterDropdown />
    </div>
  );
}
