import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';

const Dashboard = () => {
  useEffect(() => {
    console.log("📊 [Dashboard.jsx] Dashboard view rendered");
  }, []);

  return (
    <div className="flex flex-col items-center justify-center text-center min-h-[calc(100vh-80px)] px-6 bg-zinc-900 text-white">
      <h2 className="text-4xl font-extrabold mb-4">Welcome to MapEm</h2>
      <p className="text-lg text-gray-300 max-w-xl">
        Discover your family's journey through time and space. Upload a GEDCOM file to begin visualizing ancestral movements.
      </p>

      <NavLink
        to="/upload"
        className="mt-6 bg-amber-500 text-black px-6 py-3 rounded-xl text-lg font-semibold shadow-lg hover:bg-amber-600 transition"
      >
        📤 Upload Your GEDCOM
      </NavLink>

      {/* ✅ Tailwind test block */}
      <div className="mt-8 bg-green-500 text-white p-4 rounded-lg shadow">
        ✅ If this block is green, Tailwind is working.
      </div>
    </div>
  );
};

export default Dashboard;
