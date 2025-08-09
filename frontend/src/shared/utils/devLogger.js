/* Lightweight logger utilities (dev-only no-ops in production) */
export const devWarn = (...args) => {
  if (import.meta.env?.MODE !== 'production') {
    // eslint-disable-next-line no-console
    console.warn('[DEV]', ...args);
  }
};

export const devTime = (label, fn) => {
  const start = performance.now();
  try {
    return fn();
  } finally {
    const ms = Math.round(performance.now() - start);
    if (import.meta.env?.MODE !== 'production') {
      // eslint-disable-next-line no-console
      console.log(`[⏱️ perf] ${label}: ${ms}ms`);
    }
  }
};

// src/shared/utils/devLogger.js

export const devLog = (tag, msg, data = {}) => {
  if (import.meta.env.DEV) {
    const time = new Date().toLocaleTimeString();
    console.log(`[🛠️ ${tag}] ${msg} @ ${time}`, data);
  }
};
