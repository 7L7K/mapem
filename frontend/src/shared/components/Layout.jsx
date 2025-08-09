// frontend/src/shared/components/Layout.jsx
import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import Header from "@shared/components/Header";
import FilterHeader from "@shared/components/Header/FilterHeader";

/**
 * App-level shell:
 *   • Global Header (logo + nav tabs)
 *   • Optional page-specific controls (e.g. Map filter/search bar)
 *   • Routed page content
 */
export default function Layout() {
  const { pathname } = useLocation();

  // no pageControls by default; Map page renders its own floating controls
  const headerControls = null;

  return (
    <div className="h-screen flex flex-col bg-background text-white">
      {/* Global navigation bar */}
      <Header pageControls={headerControls} />

      {/* Page content (fills remaining space) */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
