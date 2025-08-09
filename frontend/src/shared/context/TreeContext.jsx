// frontend/src/shared/context/TreeContext.jsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
} from "react";
import { useLocation } from "react-router-dom";
import * as api from "@lib/api/api";

export const TreeContext = createContext({
  tree: null,
  treeId: null,
  setTreeId: () => { },
  allTrees: [],
  loading: true,
  treeName: "Unknown Tree",
});

export const useTree = () => useContext(TreeContext);

export function TreeProvider({ children }) {
  const location = useLocation();

  const [treeId, setTreeIdRaw] = useState(null);
  const [allTrees, setAllTrees] = useState([]);
  const [loading, setLoading] = useState(true);

  // Keep localStorage in-sync
  const setTreeId = (id) => {
    setTreeIdRaw(id);
    if (id) localStorage.setItem("lastTreeId", id);
    else localStorage.removeItem("lastTreeId");
  };

  /* ───── 1. grab :treeId from the URL whenever it changes ───── */
  useEffect(() => {
    const match = location.pathname.match(/\/map\/([^/]+)/);
    if (match && match[1] !== treeId) {
      setTreeIdRaw(match[1]);
    }
  }, [location.pathname, treeId]);

  /* ───── 2. load tree list ───── */
  useEffect(() => {
    const saved = localStorage.getItem("lastTreeId");

    api.getTrees()
      .then((res) => {
        // Accept both shapes
        const list = Array.isArray(res) ? res
          : Array.isArray(res.trees) ? res.trees
            : [];
        console.debug("[TreeContext] 🌳 fetched trees:", list);

        setAllTrees(list);
        setLoading(false);

        if (!treeId) {
          const validIds = new Set(list.map((t) => t.uploaded_tree_id));
          if (saved && validIds.has(saved)) setTreeIdRaw(saved);
          else if (list.length) setTreeIdRaw(list[0].uploaded_tree_id);
        }
      })
      .catch((err) => {
        console.error("[TreeContext] failed to fetch trees:", err);
        setLoading(false);
      });
  }, [treeId]);

  /* ───── 3. derived values ───── */
  const tree = useMemo(() => {
    return (allTrees || []).find((t) => t.uploaded_tree_id === treeId) || null;
  }, [allTrees, treeId]);

  const treeName = tree?.name || tree?.tree_name || "Unknown Tree";

  return (
    <TreeContext.Provider
      value={{ tree, treeId, setTreeId, allTrees, loading, treeName }}
    >
      {children}
    </TreeContext.Provider>
  );
}
