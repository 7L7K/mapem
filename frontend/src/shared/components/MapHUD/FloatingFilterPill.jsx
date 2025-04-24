// src/shared/components/MapHUD/FloatingFilterPill.jsx
import React from "react";
import { useSearch } from "@shared/context/SearchContext";

export default function FloatingFilterPill() {
  const { isDrawerOpen, setIsDrawerOpen } = useSearch();

  return (
    <button
      onClick={() => setIsDrawerOpen(!isDrawerOpen)}
      aria-label="Toggle Filters"
      className="
        fixed bottom-6 right-6 z-50
        cursor-pointer
        bg-[var(--surface)]/80 backdrop-blur-md
        text-[var(--text)]
        px-3 py-1.5
        rounded-full
        shadow-lg
        hover:bg-[var(--surface)]/90
        transition
      "
    >
      ⚙️ Filters
    </button>
  );
}
