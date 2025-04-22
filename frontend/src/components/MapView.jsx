// src/components/MapView.jsx
import React, { useMemo } from 'react';
import MigrationMap  from './Map/MigrationMap';
import PersonDrawer  from './Map/PersonDrawer';
import Legend        from './Map/Legend';
import FloatingHUD   from './FloatingHUD';
import { useSearch } from '/context/SearchContext';
import FilterHeader  from './Header/FilterHeader';

export default function MapView({ movements = [], mapCenter = [37.8, -96] }) {
  const {
    selectedPerson, setSelectedPerson,
    filters, query, mode, decade, wholeTree,
  } = useSearch();

  const filtered = useMemo(() => {
    return movements.filter(mv => {
      const year = +mv.year;
      if (!wholeTree && mode === 'person' && selectedPerson && mv.person_id !== selectedPerson.id) return false;
      if (query && !mv.person_name.toLowerCase().includes(query.toLowerCase())) return false;
      if (!filters.eventTypes[mv.event_type.toLowerCase()]) return false;
      if (!filters.vague && (!mv.latitude || !mv.longitude)) return false;
      if (!isNaN(year) && (year < decade[0] || year > decade[1])) return false;
      return true;
    });
  }, [movements, filters, query, mode, selectedPerson, decade, wholeTree]);

  return (
    <div className="flex flex-col w-full h-[calc(100vh-64px)] bg-black text-white">

      {/* 🧠 Docked Glass Filter Header */}
      <div className="px-4 pt-4 pb-2">
        <FilterHeader />
      </div>

      {/* 🗺️ Main Map */}
      <div className="relative flex-grow">
        <MigrationMap
          movements={filtered}
          center={mapCenter}
          onMarkerClick={(id) => {
            const p = movements.find((x) => x.person_id === id);
            if (p) setSelectedPerson(p);
          }}
          activePersonIds={selectedPerson ? new Set([selectedPerson.id]) : new Set()}
        />

        {/* 🧾 Legend & HUD */}
        <Legend movements={filtered} className="absolute bottom-6 left-6 z-30" />
        <FloatingHUD selectedPersonName={selectedPerson?.name} onReset={() => setSelectedPerson(null)} />
      </div>

      {/* 🙋 Person Drawer */}
      {selectedPerson && (
        <PersonDrawer
          personId={selectedPerson.id}
          personName={selectedPerson.name}
          movements={filtered.filter(m => m.person_id === selectedPerson.id)}
          onClose={() => setSelectedPerson(null)}
        />
      )}
    </div>
  );
}
