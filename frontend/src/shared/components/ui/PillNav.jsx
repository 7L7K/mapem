import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import TabLink from "./TabLink";

const routes = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Map", to: "/map" },
  { label: "Timeline", to: "/timeline" },
  { label: "People", to: "/people" },
];

export default function PillNav() {
  const loc = useLocation();

  useEffect(() => {
    console.log("🧭 [PillNav] Mounted. Current path:", loc.pathname);
  }, []);

  return (
    <div className="flex flex-wrap gap-1 bg-gray-200 rounded-lg shadow-inner px-1 py-1 w-[300px]">
      {routes.map(({ label, to }) => (
        <TabLink key={to} to={to} label={label} currentPath={loc.pathname} />
      ))}
    </div>
  );
}
