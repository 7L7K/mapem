// src/components/FloatingNav.jsx
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const tabs = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Map', path: '/map' },
  { label: 'Timeline', path: '/timeline' },
  { label: 'People', path: '/people' },
];

export default function FloatingNav() {
  const navigate = useNavigate();
  const location = useLocation();
  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-black/80 backdrop-blur-md rounded-full p-1 flex gap-1 shadow-lg z-50">
      {tabs.map(tab => {
        const active = location.pathname === tab.path;
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`px-4 py-2 rounded-full transition-all ${
              active ? 'bg-white text-black shadow' : 'text-white/60 hover:bg-white/10'
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}