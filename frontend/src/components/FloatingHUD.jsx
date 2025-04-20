// frontend/src/components/FloatingHUD.jsx
import React from "react";
import Button from "./ui/Button";

export default function FloatingHUD({
  onReset,
  selectedPersonName,
}) {
  return (
    <div className="absolute bottom-6 right-6 flex flex-col items-end gap-3 z-20">
      {selectedPersonName && (
        <div className="bg-surface border border-border text-text rounded-md px-4 py-2 shadow">
          Viewing: <strong>{selectedPersonName}</strong>
        </div>
      )}
      <Button variant="secondary" onClick={onReset}>
        🔄 Reset View
      </Button>
    </div>
  );
}
