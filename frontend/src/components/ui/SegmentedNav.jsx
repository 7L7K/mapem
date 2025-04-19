import React from "react";
import { useNavigate, useLocation } from "react-router-dom";

const tabs = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Map", path: "/map" },
  { label: "Timeline", path: "/timeline" },
  { label: "People", path: "/people" },
];

export default function SegmentedNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="flex bg-[#1a1a1a] rounded-xl p-1 gap-1 shadow-md border border-zinc-800">
      {tabs.map(({ label, path }, i) => {
        const isActive = location.pathname === path;

        return (
          <button
            key={label}
            onClick={() => navigate(path)}
            className={`relative w-[100px] h-[48px] text-[13px] tracking-wider uppercase font-semibold
              flex items-center justify-center rounded-md transition-all duration-150
              ring-1 ring-zinc-800
              ${
                isActive
                  ? "bg-[#161b22] text-sky-300 shadow-[inset_0_1px_4px_rgba(0,0,0,0.9),_0_0_12px_1px_rgba(56,189,248,0.5)] ring-2 ring-sky-400 animate-pulse-glow"
                  : "bg-gradient-to-b from-[#333] to-[#242424] text-zinc-400 hover:bg-[#2a2a2a] hover:text-white"
              }
              ${i === 0 ? "rounded-l-lg" : ""}
              ${i === tabs.length - 1 ? "rounded-r-lg" : ""}
            `}
          >
            <span
              className={`relative z-10 ${
                isActive
                  ? "text-sky-300 drop-shadow-[0_0_6px_rgba(56,189,248,0.7)]"
                  : ""
              }`}
            >
              {label}
            </span>
            {isActive && (
              <span className="absolute inset-0 rounded-md bg-gradient-to-b from-transparent via-sky-300/10 to-transparent blur-sm opacity-50 z-0 pointer-events-none" />
            )}
          </button>
        );
      })}
    </div>
  );
}
