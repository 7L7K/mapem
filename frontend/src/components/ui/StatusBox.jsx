import React from "react";
import clsx from "clsx";

export default function StatusBox({ type = "success", children }) {
  const colorMap = {
    success: "bg-success text-black",
    error: "bg-error text-white",
  };

  return (
    <div className={clsx("px-4 py-2 rounded border", colorMap[type])}>
      {children}
    </div>
  );
}
