// src/components/Header/FilterTrigger.jsx
import React from "react";
import { Sliders } from "lucide-react";
import { useSearch } from "@shared/context/SearchContext";
export default function FilterTrigger() {
  const { toggleFilters } = useSearch();

  return (
    <button
      onClick={toggleFilters}
      className="
        flex items-center gap-1
        px-3 py-1.5 text-sm text-white
        rounded-full bg-white/10 border border-white/10
        hover:bg-white/20 transition
      "
    >
      <Sliders className="w-4 h-4" />
      <span className="hidden sm:inline">Filters</span>
    </button>
  );
}
