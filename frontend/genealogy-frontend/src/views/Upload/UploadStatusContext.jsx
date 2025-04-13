import React, { createContext, useState } from 'react';

export const UploadStatusContext = createContext();

export const UploadStatusProvider = ({ children }) => {
  const [status, setStatus] = useState(null);     // current status text
  const [visible, setVisible] = useState(false);  // whether overlay is showing

  return (
    <UploadStatusContext.Provider value={{ status, setStatus, visible, setVisible }}>
      {children}
    </UploadStatusContext.Provider>
  );
};
