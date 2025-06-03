// frontend/src/shared/components/TreeSelectorDropdown.jsx
import React, { useEffect, useState } from "react";
import { useTree } from "../context/TreeContext";
import * as api from "@lib/api/api";

export default function TreeSelectorDropdown() {
  const { treeId, setTreeId } = useTree();
  const [trees, setTrees] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.getTrees().then(setTrees).catch(console.error);
  }, []);

  const selected = trees.find((t) => t.tree_id === treeId);

  return (
    <div className="relative z-50 inline-block text-left">
      <button
        onClick={() => setOpen(!open)}
        className="bg-red-600 text-white font-semibold px-3 py-1 rounded shadow hover:bg-red-700 transition"
      >
        {selected?.tree_name || "Select Tree"}
      </button>

      {open && (
        <div className="absolute mt-2 w-64 bg-black border border-gray-700 rounded shadow-lg max-h-60 overflow-auto">
          {trees.map((tree) => (
            <div
              key={tree.tree_id}
              onClick={() => {
                setTreeId(tree.uploaded_tree_id);
                setOpen(false);
              }}
              className={`px-3 py-2 cursor-pointer text-white hover:bg-gray-800 ${
                tree.uploaded_tree_id === treeId ? "bg-gray-800 font-bold" : ""
              }`}
            >
              {tree.tree_name} <span className="text-sm text-gray-400">v{tree.version_number}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
