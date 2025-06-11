import React, { useEffect } from "react";
import SystemSnapshot from "../components/SystemSnapshot";

export default function Analytics() {
  useEffect(() => {
    if (import.meta.env.DEV) console.log("📊 [Analytics] mounted");
  }, []);
  return (
    <div className="p-6 space-y-6">
      <SystemSnapshot />
      <div>
        <h2 className="text-2xl font-bold mb-4">Analytics (Coming Soon)</h2>
        <p className="text-neutral-400">
          Migration stats, unresolved location metrics, and insights will live
          here.
        </p>
      </div>
    </div>
  );
}
