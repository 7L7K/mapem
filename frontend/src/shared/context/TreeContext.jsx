import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import * as api from "@lib/api/api";

// ─────────────────────────────────────────────
// Tree Context
// ─────────────────────────────────────────────

export const TreeContext = createContext({
  tree: null,
  treeId: null,
  setTreeId: () => {},
  allTrees: [],
  loading: true,
  treeName: "Unknown Tree",
});

export const useTree = () => useContext(TreeContext);

export function TreeProvider({ children }) {
  const [treeId, setTreeIdRaw] = useState(null);
  const [allTrees, setAllTrees] = useState([]);
  const [loading, setLoading] = useState(true);

  // Smart setter with localStorage sync
  const setTreeId = (id) => {
    console.debug("[TreeContext] 🔁 setTreeId called with:", id);
    setTreeIdRaw(id);
    if (id) {
      window.localStorage.setItem("lastTreeId", String(id));
      console.debug("[TreeContext] 💾 saved treeId to localStorage:", id);
    } else {
      localStorage.removeItem("lastTreeId");
      console.debug("[TreeContext] 🧹 removed stale treeId from localStorage");
    }
  };

  useEffect(() => {
    const saved = window.localStorage.getItem("lastTreeId");
    console.debug("[TreeContext] 🔍 Checking saved treeId:", saved);

    api.getTrees()
      .then((trees) => {
        console.debug("[TreeContext] 🌳 fetched trees:", trees);
        setAllTrees(trees);
        setLoading(false);

        const validIds = new Set(trees.map(t => String(t.id)));

        if (saved && validIds.has(saved)) {
          console.debug("[TreeContext] ✅ saved treeId is valid:", saved);
          setTreeIdRaw(saved);
        } else if (trees.length > 0) {
          const fallback = String(trees[0].id);
          console.warn("[TreeContext] ❗ invalid or missing treeId — falling back to:", fallback);
          setTreeId(fallback);
        } else {
          console.warn("[TreeContext] ⚠️ no trees available");
          setTreeId(null);
        }
      })
      .catch((err) => {
        console.error("[TreeContext] ❌ failed to fetch trees:", err);
        setLoading(false);
      });
  }, []);

  // Memoize the selected tree object for fast lookups
  const tree = useMemo(
    () => allTrees.find((t) => String(t.id) === String(treeId)) || null,
    [allTrees, treeId]
  );

  const treeName = tree?.tree_name || "Unknown Tree";

  return (
    <TreeContext.Provider value={{ tree, treeId, setTreeId, allTrees, loading, treeName }}>
      {children}
    </TreeContext.Provider>
  );
}
