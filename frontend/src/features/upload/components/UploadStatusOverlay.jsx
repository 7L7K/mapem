// frontend/src/features/upload/components/UploadStatusOverlay.jsx
import React, { useContext } from "react";
import { UploadStatusContext } from "@shared/context/UploadStatusContext";

export default function UploadStatusOverlay() {
  const { visible, status } = useContext(UploadStatusContext);

  if (!visible) return null;

  const getIcon = () => {
    if (status?.startsWith("✅")) return "✅";
    if (status?.startsWith("❌")) return "❌";
    if (status?.startsWith("📤")) return "📤";
    if (status?.startsWith("🧬")) return "🧬";
    if (status?.startsWith("🌍")) return "🌍";
    return "🔄";
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center animate-fade-in">
      <div className="bg-surface border border-border text-text rounded-xl px-6 py-5 shadow-xl w-[90%] max-w-md text-center animate-pulse-glow">
        <div className="text-4xl mb-2">{getIcon()}</div>
        <div className="text-lg font-semibold tracking-wide">{status || "Processing..."}</div>
      </div>
    </div>
  );
}
