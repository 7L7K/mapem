// frontend/src/shared/context/UploadStatusContext.jsx

import React, { createContext, useContext, useState, useEffect } from "react";

// ✅ EXPORT IT — don't forget this
export const UploadStatusContext = createContext({
  visible: false,
  status: "",
  setVisible: () => {},
  setStatus: () => {},
});

// 🧠 Hook for clean usage
export const useUploadStatus = () => {
  const ctx = useContext(UploadStatusContext);
  if (!ctx) throw new Error("useUploadStatus must be used within UploadStatusProvider");
  return ctx;
};

// 👑 Provider logic — listens for global events
export function UploadStatusProvider({ children }) {
  const [visible, setVisible] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const onUploadEvent = (e) => {
      setVisible(true);
      setStatus(e.detail.status || "Uploading...");
      if (e.detail.done) {
        setTimeout(() => setVisible(false), 1500);
      }
    };

    window.addEventListener("uploadStatus", onUploadEvent);
    return () => window.removeEventListener("uploadStatus", onUploadEvent);
  }, []);

  return (
    <UploadStatusContext.Provider value={{ visible, status, setVisible, setStatus }}>
      {children}
    </UploadStatusContext.Provider>
  );
}
