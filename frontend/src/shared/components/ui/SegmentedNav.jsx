// frontend/src/components/ui/SegmentedNav.jsx
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
    <div className="w-full flex justify-center">
      <div className="flex bg-surface rounded-xl p-1 gap-1 shadow-md border border-border">
        {tabs.map(({ label, path }, i) => {
          const isActive = location.pathname === path;

          return (
            <button
              key={label}
              onClick={() => navigate(path)}
              className={`relative w-[100px] h-[48px] text-[13px] tracking-wider uppercase font-semibold
                flex items-center justify-center rounded-md transition-all duration-150
                ring-1 ring-border
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
                    : "text-dim"
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
  );
}
