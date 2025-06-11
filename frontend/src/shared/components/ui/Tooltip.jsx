import React from "react";

/**
 * Tooltip – wrap any child; shows title on hover.
 * Usage: <Tooltip text="Hello"><button>Info</button></Tooltip>
 */
export default function Tooltip({ text, children }) {
  return (
    <span className="relative group">
      {children}
      <span className="pointer-events-none absolute left-1/2 top-full z-50 mt-1 w-max -translate-x-1/2 scale-0 transform whitespace-nowrap rounded bg-black px-2 py-1 text-xs text-white opacity-0 transition-all group-hover:scale-100 group-hover:opacity-100">
        {text}
      </span>
    </span>
  );
}
code