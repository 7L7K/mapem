// src/components/Header/ModeDisplay.jsx
import React from "react";
import { useSearch } from "@shared/context/SearchContext";
export default function ModeDisplay() {
  const { mode } = useSearch();
  const modeIcon = mode === "person" ? "👤" : mode === "family" ? "🏡" : "👥";
  const modeLabel = mode.charAt(0).toUpperCase() + mode.slice(1);

  return (
    <div
      className="
        flex items-center gap-1.5
        text-sm text-white/90
        bg-white/5 px-2.5 py-1 rounded-full
        border border-white/10 shadow-sm
      "
    >
      <span className="text-base">{modeIcon}</span>
      <span>{modeLabel} View</span>
    </div>
  );
}
