import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import SegmentedNav from "./ui/SegmentedNav";
import TabLink from "./ui/TabLink";

export default function Header() {
  const loc = useLocation();

  useEffect(() => {
    console.log("🚀 [Header] Mounted.");
  }, []);

  useEffect(() => {
    console.log("🌍 [Header] Location changed:", loc.pathname);
  }, [loc.pathname]);

  return (
    <header className="bg-zinc-900 text-white px-6 py-4 border-b border-zinc-700 shadow sticky top-0 z-50">
      <div className="relative flex items-center justify-between max-w-7xl mx-auto">
        
        {/* Left: Logo */}
        <div className="flex items-center gap-2 z-10">
          <span className="text-2xl text-white">🧬</span>
          <h1 className="text-xl font-bold tracking-wide text-white drop-shadow-sm">
            MapEm
          </h1>
        </div>

        {/* Center: Segmented Nav */}
        <div className="absolute left-1/2 transform -translate-x-1/2 z-0">
          <SegmentedNav />
        </div>

        {/* Right: Upload CTA */}
        <div className="z-10">
          <TabLink to="/upload">📤 Upload GEDCOM</TabLink>
        </div>
      </div>
    </header>
  );
}
