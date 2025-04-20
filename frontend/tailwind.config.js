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
        display: ['"Chillax"', ...fontFamily.sans],
        sans: ['Inter', ...fontFamily.sans],
      },
      colors: {
        primary: '#14b8a6',
        accent: '#f59e0b',
        background: '#0f0f0f',
        surface: '#1a1a1a',
        text: '#ffffff',
        dim: '#a1a1aa',
        border: '#3f3f46',
        error: '#ef4444',
        success: '#22c55e',
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
        full: '9999px',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.5s ease-out both',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': {
            boxShadow: '0 0 8px rgba(255, 255, 255, 0.05)',
          },
          '50%': {
            boxShadow: '0 0 16px rgba(255, 255, 255, 0.2)',
          },
        },
        'fade-in': {
          '0%': {
            opacity: 0,
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
      },
    },
  },
}