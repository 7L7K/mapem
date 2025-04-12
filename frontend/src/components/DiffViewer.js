// DiffViewer component
import React, { useState } from 'react';
import { compareTrees } from '../services/api';

const DiffViewer = () => {
  const [newId, setNewId] = useState('');
  const [existingId, setExistingId] = useState('');
  const [diff, setDiff] = useState(null);

  const handleCompare = async () => {
    try {
      const res = await compareTrees(newId, existingId);
      setDiff(res.data.diff);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h2>Diff Viewer</h2>
      <div>
        <input
          type="text"
          placeholder="New Tree ID"
          value={newId}
          onChange={(e) => setNewId(e.target.value)}
        />
        <input
          type="text"
          placeholder="Existing Tree ID"
          value={existingId}
          onChange={(e) => setExistingId(e.target.value)}
        />
        <button onClick={handleCompare}>Compare Trees</button>
      </div>
      {diff && (
        <div>
          <h3>Differences:</h3>
          <pre>{JSON.stringify(diff, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default DiffViewer;
