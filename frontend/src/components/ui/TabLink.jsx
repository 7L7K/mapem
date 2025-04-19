import React from "react";
import { NavLink } from "react-router-dom";

export default function TabLink({ to, label, currentPath }) {
  const isActive = currentPath === to;

  return (
    <NavLink to={to} className="flex-1 text-center">
      <div
        className={`cursor-pointer flex justify-center items-center rounded-md px-3 py-2 text-sm transition-all
          ${isActive
            ? "bg-white text-gray-900 font-semibold"
            : "text-slate-600 hover:bg-gray-300"}
        `}
      >
        {label}
      </div>
    </NavLink>
  );
}
