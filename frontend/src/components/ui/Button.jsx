import React from "react";
import clsx from "clsx";

export default function Button({
  children,
  variant = "primary", // 'primary', 'secondary', 'text'
  className = "",
  ...props
}) {
  const base = "px-4 py-2 rounded-xl font-semibold transition-all duration-300";
  const variants = {
    primary: "bg-primary text-black hover:scale-105 hover:shadow-lg",
    secondary: "bg-surface border border-border text-text hover:bg-surface/80",
    text: "text-dim hover:text-white",
  };

  return (
    <button
      className={clsx(base, variants[variant], className)}
      {...props}
    >
      {children}
    </button>
  );
}
