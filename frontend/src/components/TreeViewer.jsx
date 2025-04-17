// src/components/TreeViewer.jsx
import React, { useEffect, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { getTree } from '../services/api';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import { useTree } from '../context/TreeContext';

cytoscape.use(dagre);

const TreeViewer = () => {
  const { treeId } = useTree();
  const [elements, setElements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!treeId) return;

    setLoading(true);
    setError(null);
    console.log("📡 Fetching tree metadata...");

    getTree(treeId)
      .then(res => {
        const elems = res?.data?.elements ?? [];
        console.log("📦 Tree metadata:", res.data);
        setElements(Array.isArray(elems) ? elems : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("❌ Error loading tree data:", err);
        setError("Failed to load tree data.");
        setLoading(false);
      });
  }, [treeId]);

  useEffect(() => {
    if (loading || error || !Array.isArray(elements) || elements.length === 0) return;

    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements,
      layout: { name: 'dagre' },
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': '#222',
            color: '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
          },
        },
      ],
    });

    return () => cy.destroy();
  }, [elements, loading, error]);

  if (loading) return <Loader />;
  if (error) return <ErrorBox message={error} />;
  if (!Array.isArray(elements) || elements.length === 0)
    return <div style={{ padding: '1rem' }}>🫥 No tree data found for this version.</div>;

  return (
    <div>
      <h2>🌳 Family Tree Viewer</h2>
      <div id="cy" style={{ width: '100%', height: '600px' }}></div>
    </div>
  );
};

export default TreeViewer;
