// src/shared/components/Header/FilterHeader.jsx
import React from 'react';
export default function FilterHeader({ children }) {
  return <div className="flex items-center gap-3 bg-[rgba(17,17,17,0.85)] backdrop-blur-md rounded-2xl px-3 py-2 shadow-lg">{children}</div>;
}
