// colors.js
const palette = [
    '#ef4444', '#3b82f6', '#10b981', '#f59e0b',
    '#6366f1', '#14b8a6', '#a855f7', '#f97316',
    '#0ea5e9', '#ec4899',
  ];
  
  export const colorForPerson = (id) => palette[id % palette.length];
  