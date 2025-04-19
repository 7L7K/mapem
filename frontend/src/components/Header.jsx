// frontend/src/components/Header.jsx
import React, { useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";

export default function Header() {
  const loc = useLocation();

  useEffect(() => {
    console.log("🧭 [Header.jsx] Rendering for route:", loc.pathname);
  }, [loc.pathname]);

  const navClass = ({ isActive }) =>
    isActive
      ? "text-white border-b-2 border-amber-500 pb-1"
      : "text-gray-300 hover:text-white transition";

  return (
    <header className="bg-zinc-900 text-white px-6 py-4 border-b border-zinc-700 shadow sticky top-0 z-50">
      <div className="flex items-center justify-between">
        {/* Left: Logo + Title */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧬</span>
          <h1 className="text-xl font-bold tracking-wide">MapEm</h1>
        </div>

        {/* Center: Nav Tabs with real gap */}
        <nav className="flex gap-6 text-sm font-medium">
          <NavLink to="/dashboard" className={navClass}>Dashboard</NavLink>
          <NavLink to="/map" className={navClass}>Map</NavLink>
          <NavLink to="/timeline" className={navClass}>Timeline</NavLink>
          <NavLink to="/people" className={navClass}>People</NavLink>
        </nav>

        {/* Right: Upload CTA */}
        <NavLink
          to="/upload"
          className="bg-amber-500 text-black px-4 py-2 rounded-lg text-sm font-semibold shadow hover:bg-amber-600 transition"
        >
          📤 Upload GEDCOM
        </NavLink>
      </div>
    </header>
  );
}
