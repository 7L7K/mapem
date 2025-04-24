import React, { useState } from "react";

const frameworks = ["HTML", "React", "Vue"];

export default function FrameworkToggle({ defaultValue = "HTML", onChange }) {
  const [selected, setSelected] = useState(defaultValue);

  const handleClick = (value) => {
    setSelected(value);
    onChange?.(value);
  };

  return (
    <div className="flex items-center gap-1 bg-zinc-800 rounded-lg px-1 py-1 shadow-inner w-[260px]">
      {frameworks.map((label) => (
        <button
          key={label}
          onClick={() => handleClick(label)}
          className={`flex-1 text-center rounded-md px-3 py-1 text-sm transition-all
            ${selected === label
              ? "bg-zinc-100 text-zinc-900 font-semibold"
              : "text-slate-300 hover:bg-zinc-700"}
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
