// frontend/src/shared/context/SearchContext.jsx
import React, { createContext, useContext, useState, useRef, useEffect } from 'react';
import { diff } from 'deep-diff';
import { devLog } from "@shared/utils/devLogger";

const SearchContext = createContext();

export const useSearch = () => useContext(SearchContext); // ⬅️ Export useSearch hook here

export function SearchProvider({ children }) {
  const [filters, setFilters] = useState({
    selectedPersonId: null,
    yearRange: [1800, 2000],
    eventTypes: [],
    vague: false,
    relations: {},
    sources: [],
  });

  const [mode, setMode] = useState('default');

  const prevRef = useRef(filters);

  useEffect(() => {
    const prev = prevRef.current;
    const changes = diff(prev, filters);
    if (changes?.length) {
      const ts = new Date().toLocaleTimeString();
      devLog('SearchContext', `🔍 filters changed @${ts}`, changes);
    }
    prevRef.current = filters;
  }, [filters]);

  return (
    <SearchContext.Provider value={{ filters, setFilters, mode, setMode }}>
      {children}
    </SearchContext.Provider>
  );
}
