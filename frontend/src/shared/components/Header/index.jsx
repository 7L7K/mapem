// src/components/Header.jsx
import React, { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import TreeSelector from "./TreeSelector";

const tabs = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Map", path: "/map" },
  { label: "Timeline", path: "/timeline" },
  { label: "People", path: "/people" },
    { label: "Geocode",   path: "/geocode" }, // 👈🏾 this one!

];

export default function Header({ pageControls = null }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (import.meta.env.DEV) console.log("🌍 [Header] Path:", pathname);
  }, [pathname]);

  return (
  <header className="sticky top-0 z-50 bg-[rgba(17,17,17,0.9)] backdrop-blur-md px-6 py-2 text-white">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      {/* Left: Logo */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-2xl">🧬</span>
        <h1 className="text-xl font-bold tracking-wide">MapEm</h1>
      </div>

      {/* Center: Nav Tabs */}
      <div className="flex justify-center flex-grow">
        <div className="flex bg-[#1f1f1f] rounded-xl p-1 gap-1 shadow-md border border-zinc-700">
          {tabs.map(({ label, path }, i) => {
            const isActive = pathname === path;
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={`relative w-[100px] h-[40px] text-xs tracking-wider uppercase font-semibold
                  flex items-center justify-center rounded-md transition-all duration-150
                  ring-1 ring-zinc-700
                  bg-gradient-to-b from-[#2a2a2a] to-[#1e1e1e]
                  hover:bg-[#2c2c2c] hover:text-white
                  ${i === 0 ? "rounded-l-lg" : ""}
                  ${i === tabs.length - 1 ? "rounded-r-lg" : ""}
                `}
              >
                <span
                  className={`relative z-10 ${
                    isActive
                      ? "text-white drop-shadow-[0_0_6px_rgba(255,255,255,0.7)]"
                      : "text-zinc-400"
                  }`}
                >
                  {label}
                </span>
                {isActive && (
                  <span className="absolute inset-0 rounded-md bg-gradient-to-b from-transparent via-white/5 to-transparent blur-sm opacity-40 z-0 pointer-events-none" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: Dynamic Controls */}
      <div className="flex items-center gap-3 shrink-0">
      <TreeSelector />
        {pageControls}
      </div>
    </div>
  </header>
    );
  }
