// src/components/TreeSelector.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useTree } from '../context/TreeContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

const TreeSelector = () => {
  const { treeId, setTreeId } = useTree();
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTree, setSelectedTree] = useState(null);

  useEffect(() => {
    console.log("📡 Fetching tree list...");
    axios.get(`${API_BASE_URL}/api/trees`)
      .then(res => {
        const treeList = res.data || [];
        setTrees(treeList);
        setLoading(false);

        if (treeList.length === 0) {
          console.warn("🪵 No trees available.");
          localStorage.removeItem("selectedTreeId");
          return;
        }

        // Try restoring saved treeId
        const savedTreeId = parseInt(localStorage.getItem("selectedTreeId"), 10);
        const isValid = treeList.some(t => t.id === savedTreeId);

        if (isValid) {
          console.log(`🌲 Restoring saved treeId: ${savedTreeId}`);
          setSelectedTree(savedTreeId);
          setTreeId(savedTreeId);
        } else {
          const fallbackId = treeList[treeList.length - 1].id;
          console.warn(`⚠️ Invalid saved treeId (${savedTreeId}). Falling back to: ${fallbackId}`);
          localStorage.setItem("selectedTreeId", fallbackId);
          setSelectedTree(fallbackId);
          setTreeId(fallbackId);
        }
      })
      .catch(err => {
        console.error("❌ Failed to load tree list:", err);
        setLoading(false);
      });
  }, []);

  const handleChange = (e) => {
    const newId = parseInt(e.target.value, 10);
    localStorage.setItem("selectedTreeId", newId);
    setSelectedTree(newId);
    setTreeId(newId);
  };

  if (loading) return <div>Loading trees...</div>;

  return (
    <div className="tree-selector">
      <label htmlFor="treeSelect">🌳 Select Tree:</label>
      <select id="treeSelect" value={selectedTree || ''} onChange={handleChange}>
        {trees.map(tree => (
          <option key={tree.id} value={tree.id}>
            {tree.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TreeSelector;
