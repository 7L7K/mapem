// TreeViewer component
import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const TreeViewer = () => {
  const cyRef = useRef(null);

  useEffect(() => {
    cyRef.current = cytoscape({
      container: document.getElementById('cy'),
      elements: [
        // Sample nodes and edges; these should be replaced with dynamic data.
        { data: { id: 'a', label: 'John Smith' } },
        { data: { id: 'b', label: 'Jane Doe' } },
        { data: { id: 'ab', source: 'a', target: 'b' } }
      ],
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': '#0074D9'
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#ccc'
          }
        }
      ],
      layout: { name: 'grid' }
    });
  }, []);

  return (
    <div>
      <h2>Family Tree Viewer</h2>
      <div id="cy" style={{ width: '800px', height: '600px' }}></div>
    </div>
  );
};

export default TreeViewer;
