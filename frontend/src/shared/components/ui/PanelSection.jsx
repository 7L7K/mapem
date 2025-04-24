import React from "react";
import clsx from "clsx";

export default function PanelSection({ title, children, className = "" }) {
  return (
    <section className={clsx("space-y-2", className)}>
      {title && <h2 className="text-xl font-display text-text">{title}</h2>}
      <div className="space-y-4">{children}</div>
    </section>
  );
}
