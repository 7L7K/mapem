import React from 'react';
import * as Slider from '@radix-ui/react-slider';
import { useSearch } from '@shared/context/SearchContext'
export default function DecadeSlider() {
  const { decade, setDecade } = useSearch();

  const handleChange = (val) => {
    setDecade(val);
  };

  const marks = [];
  for (let y = 1900; y <= 2020; y += 10) {
    const left = ((y - 1900) / (2020 - 1900)) * 100;
    marks.push(
      <div
        key={y}
        className="absolute top-0 h-full text-[10px] text-dim flex flex-col items-center"
        style={{ left: `${left}%`, transform: 'translateX(-50%)' }}
      >
        <div className="h-2 w-[2px] bg-border" />
        <span className="mt-1">{y}</span>
      </div>
    );
  }

  return (
    <div className="relative py-3 w-full">
      {/* Marks */}
      <div className="absolute top-0 left-0 right-0 h-full pointer-events-none z-10">
        {marks}
      </div>

      {/* Radix Slider */}
      <Slider.Root
        className="relative flex items-center select-none touch-none h-6 w-full z-20"
        min={1900}
        max={2020}
        step={10}
        value={decade}
        onValueChange={handleChange}
      >
        <Slider.Track className="bg-border relative grow rounded-full h-[4px]">
          <Slider.Range className="absolute bg-accent rounded-full h-full" />
        </Slider.Track>
        {decade.map((val, i) => (
          <Slider.Thumb
            key={i}
            className="block w-4 h-4 bg-accent border-2 border-white rounded-full shadow transition-all focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
        ))}
      </Slider.Root>
    </div>
  );
}
