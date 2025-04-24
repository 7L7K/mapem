import React from "react";
import clsx from "clsx";

export default function GlowPulse({ children, className = "" }) {
  return (
    <div className={clsx("animate-pulse-glow", className)}>
      {children}
    </div>
  );
}
