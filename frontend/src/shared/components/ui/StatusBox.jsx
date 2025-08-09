import React from "react";
import clsx from "clsx";

export default function StatusBox({ status = "ok", message = "", children }) {
  const color =
    status === "error" ? "bg-red-500/10 text-red-300 border-red-700/30" :
      status === "warn" ? "bg-amber-500/10 text-amber-200 border-amber-700/30" :
        "bg-emerald-500/10 text-emerald-200 border-emerald-700/30";
  return (
    <div className={clsx("rounded-md border px-3 py-2 text-sm", color)} role="status" aria-live="polite">
      {message || children}
    </div>
  );
}
