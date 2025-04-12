// src/components/TreeSelector.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useTree } from '../context/TreeContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

const TreeSelector = () => {
  const { treeId, setTreeId } = useTree();
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("📡 Fetching tree list...");
    axios.get(`${API_BASE_URL}/api/trees`)
      .then(res => {
        console.log("✅ Tree list loaded:", res.data);
        setTrees(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("❌ Failed to fetch tree list:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading tree list...</div>;

  return (
    <div style={{ marginBottom: '1rem' }}>
      <label>Select Tree: </label>
      <select
        value={treeId}
        onChange={(e) => {
          console.log("🔄 Tree changed to:", e.target.value);
          setTreeId(Number(e.target.value));
        }}
      >
        {trees.map(tree => (
          <option key={tree.id} value={tree.id}>
            {tree.name || `Tree ${tree.id}`}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TreeSelector;
