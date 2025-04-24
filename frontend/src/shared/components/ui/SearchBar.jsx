// src/components/Header/SearchBar.jsx
import React from "react";
import { useSearch } from "@shared/context/SearchContext";
export default function SearchBar({ className = "" }) {
  const { query, setQuery } = useSearch();

  return (
    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search person..."
      className={`
        ${className}
        w-[180px] md:w-[200px] lg:w-[240px]
        bg-white/10 text-white placeholder:text-white/40
        text-sm px-4 py-1 rounded-full
        border border-white/10
        focus:outline-none focus:ring-2 focus:ring-white/30
        transition-all duration-150
      `}
    />
  );
}
