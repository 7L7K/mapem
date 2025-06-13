import React from "react";
import { useUploadStatus } from "@shared/context/UploadStatusContext";

function UploadStatusOverlay() {
  const { visible, status } = useUploadStatus();

  if (!visible) return null;

  const icon = (() => {
    if (status?.startsWith("✅")) return "✅";
    if (status?.startsWith("❌")) return "❌";
    if (status?.startsWith("📤")) return "📤";
    if (status?.startsWith("🧬")) return "🧬";
    if (status?.startsWith("🌍")) return "🌍";
    return "🔄";
  })();

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center animate-fade-in">
      <div className="bg-surface border border-border text-text rounded-xl px-6 py-5 shadow-xl w-[90%] max-w-md text-center animate-pulse-glow">
        <div className="text-4xl mb-2">{icon}</div>
        <div className="text-lg font-semibold tracking-wide">{status || "Processing..."}</div>
      </div>
    </div>
  );
}

export default UploadStatusOverlay;
