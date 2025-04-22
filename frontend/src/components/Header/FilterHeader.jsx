// src/components/Header/FilterHeader.jsx
import React from "react";
import SearchBar from "../ui/SearchBar";
import ModeSelector from "./ModeSelector";
import WholeTreeToggle from "./WholeTreeToggle";
import FilterButton from "./FilterButton";

export default function FilterHeader() {
  return (
    <div
      className="
        w-full max-w-6xl mx-auto
        px-4 py-2
        bg-[rgba(17,17,17,0.25)] backdrop-blur-md
        rounded-full shadow-sm
        flex items-center justify-between
        gap-x-3
        text-white text-sm
      "
    >
      {/* 🔍 Search */}
      <div className="flex-1">
        <SearchBar />
      </div>

      {/* 🎚️ Mode Selector */}
      <div className="flex-shrink-0">
        <ModeSelector />
      </div>

      {/* 🌳 Tree View Toggle */}
      <div className="flex-shrink-0">
        <WholeTreeToggle />
      </div>

      {/* ⚙️ Filters */}
      <div className="flex-shrink-0">
        <FilterButton />
      </div>
    </div>
  );
}
