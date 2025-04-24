// src/shared/components/MapHUD/FilterFAB.jsx
import React from "react";
import { SlidersHorizontal } from "lucide-react";
import { useSearch } from "@shared/context/SearchContext";

export default function FilterFAB() {
  const { isDrawerOpen, setIsDrawerOpen } = useSearch();

  return (
    <button
      aria-label="Open Filters"
      onClick={() => setIsDrawerOpen(!isDrawerOpen)}
      className="fixed bottom-6 right-6 z-50 rounded-full p-3 bg-[var(--surface)] text-[var(--text)] shadow-lg hover:scale-105 transition"
    >
      <SlidersHorizontal size={24} />
    </button>
  );
}
