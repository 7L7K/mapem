import React from "react";
import clsx from "clsx";

export default function Card({ children, className = "" }) {
  return (
    <div
      className={clsx(
        "bg-surface text-text border border-border rounded-xl shadow p-4",
        className
      )}
    >
      {children}
    </div>
  );
}
