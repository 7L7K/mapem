///Users/kingal/mapem/frontend/src/components/Header.jsx
import React, { useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";

// Nav items
const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/map", label: "Map" },
  { path: "/timeline", label: "Timeline" },
  { path: "/people", label: "People" },
];

export default function Header() {
  const loc = useLocation();
  useEffect(() => {
    console.log("🧭 [Header.jsx] RENDERING ✅ for:", loc.pathname);
  }, [loc.pathname]);

  return (
    <header className="bg-red-700 text-white px-6 py-4 border-b border-white shadow sticky top-0 z-50">
      <div className="flex items-center justify-between">
        {/* Left: Logo */}
        <div className="flex items-center gap-2">
          <span className="text-3xl">🧬</span>
          <h1 className="text-2xl font-bold tracking-wide">MapEm</h1>
        </div>

        {/* Center: Navigation */}
        <nav className="flex gap-6 text-sm font-medium text-blue-200">
          {navItems.map(({ path, label }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                isActive
                  ? "text-white underline underline-offset-4"
                  : "hover:text-white transition"
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Right: Upload CTA */}
        <NavLink
          to="/upload"
          className="bg-white text-black px-4 py-2 rounded-full text-sm font-semibold shadow hover:bg-gray-100 transition"
        >
          Upload GEDCOM
        </NavLink>
      </div>
    </header>
  );
}
