// frontend/src/lib/devLogger.js

export const log = (label, ...args) => {
    if (import.meta.env.DEV) {
      const time = new Date().toLocaleTimeString();
      console.log(`🛠️ [${label}] @ ${time}`, ...args);
    }
  };
  
  export const devLoggerEnabled = import.meta.env.DEV;
  