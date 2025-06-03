// src/shared/context/SearchContext.jsx
import React, {
  createContext,
  useContext,
  useState,
  useMemo,
  useEffect,
} from "react";
import { useTree } from "@shared/context/TreeContext";
import { getVisibleCounts } from "@lib/api/api";

const SearchContext = createContext(null);
export const useSearch = () => useContext(SearchContext);

const defaultFilters = {
  person: "",
  yearRange: [null, null],
  vague: true,
  eventTypes: {
    birth: true,
    death: true,
    marriage: true,
    divorce: true,
    residence: true,
  },
  relations: {},
  sources: {},
};

export function SearchProvider({ children }) {
  const { treeId: activeTreeId } = useTree();
  const [filters, setFilters] = useState(defaultFilters);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [decade, setDecade] = useState([1900, 2020]);
  const [mode, setMode] = useState('person');
  const [wholeTree, setWholeTree] = useState(false);
  const toggleWholeTree = () => setWholeTree((p) => !p);

  const [visibleCounts, setVisibleCounts] = useState({
    people: 0,
    families: 0,
    wholeTree: 0,
  });

  useEffect(() => {
    if (!activeTreeId) return;

    getVisibleCounts(activeTreeId, filters)
      .then((d) =>
        setVisibleCounts({
          people: d?.individuals ?? 0,
          families: d?.families ?? 0,
          wholeTree: d?.events?.total ?? 0,
        })
      )
      .catch((err) =>
        console.error("❌ failed to fetch visible-counts →", err.message)
      );
  }, [activeTreeId, filters]);

  const clearAll = () => setFilters(defaultFilters);

  const ctx = useMemo(
    () => ({
      filters,
      setFilters,
      isDrawerOpen,
      setIsDrawerOpen,
      decade,
      setDecade,
      mode,
      setMode,
      wholeTree,
      toggleWholeTree,
      clearAll,
      visibleCounts,
    }),
    [filters, isDrawerOpen, decade, mode, wholeTree, visibleCounts]
  );

  return (
    <SearchContext.Provider value={ctx}>{children}</SearchContext.Provider>
  );
}
