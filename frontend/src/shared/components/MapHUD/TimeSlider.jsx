import React, { useMemo } from "react";
import * as Slider from "@radix-ui/react-slider";
import { useSearch } from "@shared/context/SearchContext";

const PRESETS = [
  { label: "1850", range: [1850, 1850] },
  { label: "1880", range: [1880, 1880] },
  { label: "1900", range: [1900, 1900] },
  { label: "1910", range: [1910, 1910] },
  { label: "1920", range: [1920, 1920] },
  { label: "1930", range: [1930, 1930] },
  { label: "1940", range: [1940, 1940] },
];

export default function TimeSlider() {
  const { filters, setFilters } = useSearch();

  const value = useMemo(() => {
    const yr = filters?.yearRange || [1800, 2000];
    return [Number(yr[0]) || 1800, Number(yr[1]) || 2000];
  }, [filters?.yearRange]);

  const setRange = (range) => setFilters((prev) => ({ ...prev, yearRange: range }));

  return (
    <div className="absolute left-1/2 -translate-x-1/2 bottom-4 z-50 w-[min(800px,92vw)] bg-[rgba(17,17,17,0.85)] backdrop-blur-md rounded-2xl px-4 py-3 border border-white/10 shadow-lg">
      <div className="flex items-center gap-3 mb-2 justify-between">
        <div className="flex gap-1">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => setRange(p.range)}
              className="px-2 py-1 text-xs rounded bg-white/10 hover:bg-white/20 text-white border border-white/10"
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="text-xs text-white/70">{value[0]} — {value[1]}</div>
      </div>

      <Slider.Root
        className="relative flex items-center select-none touch-none h-6 w-full"
        min={1700}
        max={2025}
        step={1}
        value={value}
        onValueChange={setRange}
      >
        <Slider.Track className="bg-white/10 relative grow rounded-full h-[4px]">
          <Slider.Range className="absolute bg-yellow-400 rounded-full h-full" />
        </Slider.Track>
        {value.map((_, i) => (
          <Slider.Thumb
            key={i}
            className="block w-4 h-4 bg-yellow-400 border-2 border-black rounded-full shadow focus:outline-none focus:ring-2 focus:ring-yellow-300/50"
          />
        ))}
      </Slider.Root>
    </div>
  );
}

import React from 'react';
import * as Slider from '@radix-ui/react-slider';
import { useSearch } from '@shared/context/SearchContext';

export default function TimeSlider() {
  const { filters, setFilters } = useSearch();
  const value = Array.isArray(filters.yearRange) ? filters.yearRange : [1800, 2000];

  const onChange = (vals) => {
    if (!Array.isArray(vals) || vals.length !== 2) return;
    setFilters({ yearRange: [Number(vals[0]), Number(vals[1])] });
  };

  return (
    <div className="absolute left-1/2 -translate-x-1/2 bottom-3 z-[500] w-[min(640px,90vw)] px-4">
      <div className="bg-black/60 backdrop-blur rounded-xl px-4 py-2 border border-white/10">
        <div className="text-[10px] uppercase tracking-wider text-white/60 mb-1">Year Range</div>
        <Slider.Root
          className="relative flex items-center select-none touch-none h-6 w-full"
          min={1600}
          max={2025}
          step={1}
          value={value}
          onValueChange={onChange}
        >
          <Slider.Track className="bg-white/20 relative grow rounded-full h-[4px]">
            <Slider.Range className="absolute bg-accent rounded-full h-full" />
          </Slider.Track>
          {value.map((_, i) => (
            <Slider.Thumb key={i} className="block w-4 h-4 bg-white border border-black/40 rounded-full shadow focus:outline-none" />
          ))}
        </Slider.Root>
        <div className="flex justify-between text-xs text-white/70 mt-1">
          <span>{value[0]}</span>
          <span>{value[1]}</span>
        </div>
      </div>
    </div>
  );
}


