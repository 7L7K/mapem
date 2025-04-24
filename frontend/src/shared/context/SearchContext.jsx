// src/shared/context/SearchContext.jsx
import React, { createContext, useContext, useState, useMemo } from "react";

const SearchContext = createContext(null);
export const useSearch = () => useContext(SearchContext);

const defaultFilters = {
  person: "",
  yearRange: [1800, 1950],
  eventTypes: { birth: true, death: true, residence: true },
  relations: { self: true, parents: true, siblings: true, cousins: false },
  sources: { gedcom: true, census: true, manual: true, ai: false },
  vague: false,
};

export function SearchProvider({ children }) {
  const [filters, setFilters] = useState(defaultFilters);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const clearAll = () => setFilters(defaultFilters);

  const ctx = useMemo(
    () => ({
      filters,
      setFilters,
      isDrawerOpen,
      setIsDrawerOpen,
      clearAll,
    }),
    [filters, isDrawerOpen]
  );

  return (
    <SearchContext.Provider value={ctx}>{children}</SearchContext.Provider>
  );
}
