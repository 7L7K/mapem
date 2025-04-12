import React, { useContext } from 'react';
import { UploadStatusContext } from './UploadStatusContext';

const UploadStatusOverlay = () => {
  const { visible, status } = useContext(UploadStatusContext);

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.75)',
      color: '#fff',
      fontSize: '1.5rem',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'monospace'
    }}>
      <div>{status || "Processing..."}</div>
    </div>
  );
};

export default UploadStatusOverlay;
