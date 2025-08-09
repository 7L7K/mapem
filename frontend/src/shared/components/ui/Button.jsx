import React from "react";
import clsx from "clsx";

export default function Button({
  children,
  variant = "primary", // 'primary', 'secondary', 'text'
  className = "",
  type = "button",
  disabled = false,
  ...props
}) {
  const base = "px-4 py-2 rounded-xl font-semibold transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black";
  const variants = {
    primary: "bg-primary text-black hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:hover:scale-100",
    secondary: "bg-surface border border-border text-text hover:bg-surface/80 disabled:opacity-50",
    text: "text-dim hover:text-white disabled:opacity-50",
  };

  return (
    <button
      type={type}
      aria-disabled={disabled || undefined}
      className={clsx(base, variants[variant], className)}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
