import React, { useEffect, useState } from "react";
import { useTree } from "@shared/context/TreeContext";
import { getTrees } from "@lib/api/api";

export default function TreeSelector() {
  const { treeId, setTreeId } = useTree();
  const [trees, setTrees] = useState([]);

  useEffect(() => {
    console.debug("[🌳 TreeSelector] 🟡 Mounted. Fetching tree list...");
    getTrees()
      .then((data) => {
        console.debug("[🌳 TreeSelector] ✅ API returned trees:", data);
        setTrees(data);
      })
      .catch((err) => {
        console.error("[🌳 TreeSelector] ❌ Error fetching trees:", err);
      });
  }, []);

  const handleChange = (e) => {
    const newId = e.target.value; // 👈 UUID string, no Number()
    console.debug("[🌳 TreeSelector] 📥 Selected treeId:", newId);
    setTreeId(newId);
  };

  return (
    <>
      <div className="text-xs text-yellow-400">[TreeSelector loaded]</div>
      <select
        value={treeId || ""}
        onChange={handleChange}
        className="rounded-md bg-[var(--surface)] text-white px-2 py-1 text-sm"
      >
        <option value="" disabled>
          Select a tree…
        </option>
        {trees.length === 0 && (
          <option disabled>⚠️ No trees found</option>
        )}
        {trees.map((tree) => (
          <option key={tree.id} value={tree.id}>
            {tree.name}
          </option>
        ))}
      </select>
    </>
  );
}
