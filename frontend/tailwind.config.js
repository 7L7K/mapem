// frontend/tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/styles/**/*.{css}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Chillax"', ...defaultTheme.fontFamily.sans],
        sans:   ['Inter',   ...defaultTheme.fontFamily.sans],
      },
      colors: {
        primary:  '#14b8a6',
        accent:   '#f59e0b',
        background: 'var(--background)',
        surface:    'var(--surface)',
        text:       'var(--text)',
        dim:        'var(--dim)',
        border:     'var(--border)',
        error:      'var(--error)',
        success:    'var(--success)',
      },
    },
  },
};
