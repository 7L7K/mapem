// src/components/Header/SearchBar.jsx
import React from "react";
import { useSearch } from "/context/SearchContext";

export default function SearchBar({ className = "" }) {
  const { query, setQuery } = useSearch();

  return (
    <input
      type="text"
      placeholder="Search person..."
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      className={`
        ${className}
        bg-[rgba(0,0,0,0.5)]
        border border-white/10
        text-white placeholder:text-white/40
        text-sm px-4 py-1 rounded-full
        focus:outline-none focus:ring-2 focus:ring-white/30
      `}
    />
  );
}
