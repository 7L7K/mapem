// src/context/TreeContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const TreeContext = createContext();

export const TreeProvider = ({ children }) => {
  const [treeId, setTreeId] = useState(() => {
    const saved = localStorage.getItem("selectedTreeId");
    return saved ? Number(saved) : 1;
  });

  useEffect(() => {
    console.log("🌲 TreeContext: Selected treeId updated to:", treeId);
    localStorage.setItem("selectedTreeId", treeId);
  }, [treeId]);

  return (
    <TreeContext.Provider value={{ treeId, setTreeId }}>
      {children}
    </TreeContext.Provider>
  );
};

export const useTree = () => {
  const context = useContext(TreeContext);
  if (context === undefined) {
    throw new Error("`useTree` must be called within a `<TreeProvider>`");
  }
  return context;
};
