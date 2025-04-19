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
      <div className="flex items-center justify-between">
        {/* Left: Logo + Title */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧬</span>
          <h1 className="text-xl font-bold tracking-wide">MapEm</h1>
        </div>

        {/* Center: Segmented Nav */}
        <div className="flex-1 flex justify-center">
          <SegmentedNav />
        </div>

        {/* Right: Upload CTA */}
        <TabLink to="/upload">📤 Upload GEDCOM</TabLink>
      </div>
    </header>
  );
}
