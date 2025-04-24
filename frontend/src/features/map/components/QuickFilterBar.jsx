// src/features/map/components/QuickFilterBar.jsx
import React from "react";
import { useSearch } from "@shared/context/SearchContext";

export default function QuickFilterBar() {
  const { filters, setFilters, setIsDrawerOpen } = useSearch();

  const handlePersonChange = (e) =>
    setFilters((prev) => ({ ...prev, person: e.target.value }));

  const summaryPills = () => {
    const pills = [];
    const { eventTypes, relations, sources, yearRange } = filters;

    // event type summary
    const activeEvents = Object.entries(eventTypes)
      .filter(([_, v]) => v)
      .map(([k]) => k)
      .join(",");
    pills.push(`Events:${activeEvents}`);

    // year range summary
    pills.push(`${yearRange[0]}–${yearRange[1]}`);

    // vague toggle
    if (filters.vague) pills.push("Vague✔");

    return pills;
  };

  return (
    <div className="flex items-center space-x-4">
      {/* Person search */}
      <input
        type="text"
        value={filters.person}
        placeholder="Search person…"
        onChange={handlePersonChange}
        className="bg-[var(--surface)] border border-white/10 rounded px-3 py-1 w-40"
      />

      {/* Summary pills */}
      <div className="flex flex-wrap gap-1">
        {summaryPills().map((p) => (
          <span
            key={p}
            className="filter-pill bg-white/10 text-xs font-semibold"
          >
            {p}
          </span>
        ))}
      </div>

      {/* Open drawer */}
      <button
        onClick={() => setIsDrawerOpen(true)}
        className="text-sm text-accent hover:underline"
      >
        ⚙️ Filters
      </button>
    </div>
  );
}
