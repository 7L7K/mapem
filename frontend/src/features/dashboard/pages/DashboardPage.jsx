import React, { useEffect } from "react";
import { NavLink } from "react-router-dom";
import Button from "@shared/components/ui/Button";
import GlowPulse from "@shared/components/ui/GlowPulse";

export default function DashboardPage() {
  useEffect(() => {
    console.log("📊 [Dashboard.jsx] Dashboard view rendered");
  }, []);

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center text-center px-6 py-16 space-y-10">
      {/* Logo + Name */}
      <div className="flex flex-col items-center space-y-2">
        <span className="text-6xl font-display font-bold text-white drop-shadow-lg">🧬 MapEm</span>
        <span className="text-dim tracking-wide text-base uppercase">Ancestral Mapping System</span>
      </div>

      {/* Headline */}
      <div className="max-w-2xl space-y-4">
        <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight text-white">
          Trace your family's journey through time & place.
        </h1>
        <p className="text-dim text-lg leading-relaxed">
          Upload a GEDCOM file and watch your ancestors move across the world through space, time, and memory.
        </p>
      </div>

      {/* CTA */}
      <GlowPulse className="mt-2">
        <NavLink to="/upload">
          <Button variant="primary" className="text-lg px-8 py-3 rounded-full shadow-lg">
            📤 Upload Your GEDCOM
          </Button>
        </NavLink>
      </GlowPulse>

      {/* Quote */}
      <div className="text-dim text-sm italic pt-4">
        “I am my ancestors’ wildest dreams.”
      </div>
    </div>
  );
}
