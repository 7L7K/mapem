// src/components/Header.jsx
import React, { useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useTree } from "@shared/context/TreeContext";
import TreeSelector from "./TreeSelector";
import { navItems } from "@app/routes.config";

export default function Header({ pageControls = null }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { treeId } = useTree();

  useEffect(() => {
    if (import.meta.env.DEV) console.log("🌍 [Header] Path:", pathname);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 bg-[rgba(17,17,17,0.9)] backdrop-blur-md px-3 md:px-6 py-2 text-white">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <button onClick={() => navigate('/')} className="flex items-center gap-2">
            <span className="text-2xl">🧬</span>
            <h1 className="text-xl font-bold tracking-wide">MapEm</h1>
          </button>
        </div>

        {/* Center: Nav Tabs */}
        <nav className="flex justify-center flex-grow" aria-label="Primary">
          <div className="flex bg-[#1f1f1f] rounded-xl p-1 gap-1 shadow-md border border-zinc-700 overflow-x-auto max-w-full">
            {([
              // Ensure Map tab exists (auto-redirects to latest tree)
              { title: "Map", path: "/map" },
              ...navItems,
            ]
              // Remove duplicates by path
              .filter((item, idx, self) => idx === self.findIndex(it => it.path === item.path))
            ).map(({ title: label, path }, i, arr) => {
              const isActive = pathname === path || pathname.startsWith(path + "/");
              return (
                <Link
                  key={path}
                  to={path === '/map' && treeId ? `/map/${treeId}` : path}
                  onMouseEnter={() => {
                    // Prefetch when hovering route buttons (let browser cache do its thing)
                    try {
                      const link = document.createElement('link');
                      link.rel = 'prefetch';
                      link.href = path;
                      document.head.appendChild(link);
                      setTimeout(() => document.head.removeChild(link), 2000);
                    } catch { }
                  }}
                  className={`relative w-[100px] h-[40px] text-xs tracking-wider uppercase font-semibold
                  flex items-center justify-center rounded-md transition-all duration-150
                  ring-1 ring-zinc-700
                  bg-gradient-to-b from-[#2a2a2a] to-[#1e1e1e]
                  hover:bg-[#2c2c2c] hover:text-white
                  ${i === 0 ? "rounded-l-lg" : ""}
                  ${i === arr.length - 1 ? "rounded-r-lg" : ""}
                `}
                  role="tab"
                  aria-selected={isActive}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span
                    className={`relative z-10 ${isActive
                      ? "text-white drop-shadow-[0_0_6px_rgba(255,255,255,0.7)]"
                      : "text-zinc-400"
                      }`}
                  >
                    {label}
                  </span>
                  {isActive && (
                    <span className="absolute inset-0 rounded-md bg-gradient-to-b from-transparent via-white/5 to-transparent blur-sm opacity-40 z-0 pointer-events-none" />
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Right: Dynamic Controls */}
        <div className="flex items-center gap-3 shrink-0">
          <TreeSelector />
          {pageControls}
        </div>
      </div>
    </header>
  );
}
