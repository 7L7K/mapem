// src/shared/context/MapControlContext.jsx
import React, { createContext, useContext, useState, useMemo } from 'react';

const MapControlContext = createContext(null);
export const useMapControl = () => useContext(MapControlContext);

export function MapControlProvider({ children }) {
  const [activeSection, setActiveSection] = useState(null); // 'search' | 'person' | 'family' | 'compare' | 'filters' | null
  const toggleSection = (section) => setActiveSection((p) => (p === section ? null : section));
  const value = useMemo(() => ({ activeSection, toggleSection }), [activeSection]);
  return <MapControlContext.Provider value={value}>{children}</MapControlContext.Provider>;
}

