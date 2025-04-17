import React, { useState, useContext } from 'react';
import { uploadTree } from '../services/api';
import { UploadStatusContext } from './UploadStatusContext';

const UploadPanel = () => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [response, setResponse] = useState(null);

  const { setStatus, setVisible } = useContext(UploadStatusContext);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus('Please select a file first.');
      return;
    }

    setUploadStatus('Uploading...');
    setVisible(true);
    setStatus("📤 Uploading GEDCOM file...");

    try {
      const res = await uploadTree(file);

      setStatus("🧬 Parsing & saving tree...");
      await new Promise(resolve => setTimeout(resolve, 1000));

      setStatus("🌍 Geocoding locations...");
      await new Promise(resolve => setTimeout(resolve, 1000));

      setStatus("✅ Upload complete!");
      setTimeout(() => setVisible(false), 1500);

      setResponse(res.data);
      setUploadStatus('Upload successful!');
    } catch (err) {
      setStatus("❌ Upload failed.");
      setTimeout(() => setVisible(false), 1500);

      let backendTrace = "";
      try {
        const parsed = JSON.parse(err.request?.responseText);
        backendTrace = parsed?.trace || "";
        console.log("🧠 Backend Trace:\n", backendTrace);
      } catch (parseErr) {
        console.warn("⚠️ Could not parse backend trace:", parseErr);
      }

      setUploadStatus(`Upload failed: ${err.message}`);
      console.error("❌ Upload error:", err);
    } // <-- THIS was missing
  };

  return (
    <div className="panel">
      <h2>Upload GEDCOM File</h2>
      <input type="file" onChange={handleFileChange} accept=".ged,.gedcom" />
      <button onClick={handleUpload}>Upload</button>
      {uploadStatus && <p>{uploadStatus}</p>}
      {response && (
        <div className="response-box">
          <h3>Response:</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default UploadPanel;
