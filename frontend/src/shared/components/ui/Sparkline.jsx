import React from "react";

/**
 * Super-lightweight SVG sparkline.
 * Pass an array of numbers (0–1 range normalised) OR raw numbers.
 */
export default function Sparkline({ data = [], stroke = "currentColor", height = 24 }) {
  if (!data.length) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const norm = (v) => ((v - min) / (max - min || 1)) * 100;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - norm(v);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 100" width="100%" height={height} preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}
