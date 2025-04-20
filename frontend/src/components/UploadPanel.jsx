// frontend/src/components/UploadPanel.jsx
import React, { useState, useContext, useRef } from "react";
import { uploadTree } from "../services/api";
import { UploadStatusContext } from "./UploadStatusContext";

export default function UploadPanel() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [response, setResponse] = useState(null);
  const fileInputRef = useRef(null);

  const { setStatus, setVisible } = useContext(UploadStatusContext);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith(".ged")) {
      setFile(selectedFile);
      setUploadStatus("");
    } else {
      setFile(null);
      setUploadStatus("❌ Please select a `.ged` file.");
    }
  };

  const handleUpload = async () => {
    if (!file || !file.name.endsWith(".ged")) {
      setUploadStatus("❌ Please select a `.ged` file first.");
      return;
    }

    setUploadStatus("⏳ Uploading...");
    setVisible(true);
    setStatus("📤 Uploading GEDCOM file...");

    try {
      const res = await uploadTree(file);

      setStatus("🧬 Parsing & saving tree...");
      await new Promise((r) => setTimeout(r, 1000));

      setStatus("🌍 Geocoding locations...");
      await new Promise((r) => setTimeout(r, 1000));

      setStatus("✅ Upload complete!");
      setTimeout(() => setVisible(false), 1500);

      setResponse(res.data);
      setUploadStatus("✅ Upload successful!");
    } catch (err) {
      setStatus("❌ Upload failed.");
      setTimeout(() => setVisible(false), 1500);

      let trace = "";
      try {
        const parsed = JSON.parse(err.request?.responseText);
        trace = parsed?.trace || "";
        console.log("🧠 Backend Trace:\n", trace);
      } catch (parseErr) {
        console.warn("⚠️ Could not parse backend trace:", parseErr);
      }

      setUploadStatus(`❌ Upload failed: ${err.message}`);
      console.error("❌ Upload error:", err);
    }
  };

  return (
    <main className="flex flex-col items-center justify-start px-6 pt-16 pb-24 text-text max-w-3xl mx-auto">
      <h2 className="text-3xl md:text-4xl font-display font-semibold text-text mb-4 text-center">
        Upload GEDCOM File
      </h2>

      <p className="text-dim text-sm mb-8 text-center">
        Select a `.ged` file to start mapping your family’s journey.
      </p>

      <div className="w-full bg-surface rounded-xl border border-border p-6 shadow-md">
        <div className="flex flex-col items-center gap-4">
          {/* File Picker Trigger */}
          <button
            onClick={() => fileInputRef.current.click()}
            className="w-full max-w-xs bg-primary text-black px-4 py-2 rounded-md font-semibold text-sm hover:bg-teal-400 transition-all shadow"
          >
            {file ? `📄 ${file.name}` : "📂 Choose .ged File"}
          </button>

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".ged"
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            className="w-full max-w-xs bg-accent text-black px-4 py-2 rounded-md font-semibold text-sm hover:bg-yellow-400 transition-all shadow"
          >
            Upload
          </button>
        </div>

        {/* Upload Status */}
        {uploadStatus && (
          <div
            className={`mt-6 text-sm px-4 py-3 rounded-md flex items-center gap-2
              ${
                uploadStatus.startsWith("✅")
                  ? "bg-green-800 text-green-200"
                  : uploadStatus.startsWith("❌")
                  ? "bg-red-800 text-red-300"
                  : "bg-zinc-800 text-white"
              }`}
          >
            {uploadStatus}
          </div>
        )}

        {/* Upload Response */}
        {response && (
          <div className="mt-6 text-sm bg-zinc-900 rounded-lg p-4 border border-zinc-700 overflow-x-auto">
            <h3 className="font-bold mb-2 text-accent">Response:</h3>
            <pre className="text-xs text-green-400">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </main>
  );
}
