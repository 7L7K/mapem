import React from "react";
import clsx from "clsx";

// Main Card wrapper
export function Card({ children, className = "", ...props }) {
  return (
    <div
      className={clsx(
        "bg-surface text-text border border-border rounded-xl shadow p-4",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// CardContent utility wrapper (for spacing/content control)
export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={clsx("p-4", className)} {...props}>
      {children}
    </div>
  );
}
