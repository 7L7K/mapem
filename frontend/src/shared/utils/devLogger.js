// src/shared/utils/devLogger.js

export const devLog = (tag, msg, data = {}) => {
  if (import.meta.env.DEV) {
    const time = new Date().toLocaleTimeString();
    console.log(`[🛠️ ${tag}] ${msg} @ ${time}`, data);
  }
};
