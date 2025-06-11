import React from "react";

/** Simple tail-wind spinner */
export default function Spinner({ size = 6 }) {
  return (
    <div
      className={`inline-block animate-spin rounded-full border-2 border-transparent border-t-white border-r-white`}
      style={{ width: `${size * 4}px`, height: `${size * 4}px` }}
    />
  );
}
