// src/components/DiffViewer.jsx
import React, { useState } from 'react';
import Loader from '../views/ui/Loader.jsx';
import ErrorBox from '../views/ui/ErrorBox.jsx';
import { compareTrees } from '../../services/api.js';

const DiffViewer = () => {
  const [newId, setNewId] = useState('');
  const [existingId, setExistingId] = useState('');
  const [diffResult, setDiffResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCompare = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await compareTrees(newId, existingId);
      setDiffResult(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError("Failed to compare trees");
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Diff Viewer</h2>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
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
      {loading && <Loader />}
      {error && <ErrorBox message={error} />}
      {diffResult && (
        <pre>{JSON.stringify(diffResult, null, 2)}</pre>
      )}
    </div>
  );
};

export default DiffViewer;
