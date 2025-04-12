// UploadPanel component
import React, { useState } from 'react';
import { uploadTree } from '../services/api';

const UploadPanel = () => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [response, setResponse] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploadStatus('Uploading...');
    try {
      const res = await uploadTree(file);
      setResponse(res.data);
      setUploadStatus('Upload successful!');
    } catch (err) {
      setUploadStatus('Upload failed.');
      console.error(err);
    }
  };

  return (
    <div>
      <h2>Upload GEDCOM File</h2>
      <input type="file" onChange={handleFileChange} accept=".ged,.gedcom" />
      <button onClick={handleUpload}>Upload</button>
      {uploadStatus && <p>{uploadStatus}</p>}
      {response && (
        <div>
          <h3>Response:</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default UploadPanel;
