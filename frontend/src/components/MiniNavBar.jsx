// frontend/src/components/MiniNavBar.jsx
import React from "react";
import { useTree } from "../context/TreeContext";

export default function MiniNavBar({ peopleCount, eventCount }) {
  const { treeId } = useTree();

  return (
    <div className="bg-background/80 backdrop-blur-sm rounded-lg p-3 flex flex-wrap items-center justify-between text-sm text-dim shadow">
      <div>
        <strong className="text-text">Tree:</strong> {treeId || "—"}
      </div>
      <div className="flex gap-4">
        <div>
          <strong className="text-accent">{peopleCount}</strong> people
        </div>
        <div>
          <strong className="text-accent">{eventCount}</strong> events
        </div>
      </div>
    </div>
  );
}
