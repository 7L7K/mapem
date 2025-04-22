// src/components/Header/FilterButton.jsx
import { Sliders } from 'lucide-react';
import { useSearch } from '/context/SearchContext';

export default function FilterButton() {
  const { toggleFilters } = useSearch();

  return (
    <button
      onClick={toggleFilters}
      className="
        flex items-center gap-2
        px-3 py-1
        text-sm font-medium
        text-white bg-[rgba(17,17,17,0.4)]
        border border-white/20
        rounded-full shadow-sm
        hover:bg-white/10 hover:border-white/40
        transition-all
      "
    >
      <Sliders className="w-4 h-4" />
      <span>Filters</span>
    </button>
  );
}
