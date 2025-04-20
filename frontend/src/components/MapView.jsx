// src/components/MapView.jsx
import React, { useState, useMemo } from 'react';
import MigrationMap from './Map/MigrationMap';
import PersonDrawer from './Map/PersonDrawer';
import Legend from './Map/Legend';
import FloatingHUD from './FloatingHUD';
import GeneaGlassPanel from './GeneaGlassPanel';
import AdvancedFilterDrawer from './Map/AdvancedFilterDrawer';

export default function MapView({ movements: allMovements = [], mapCenter = [37.8, -96], loading, error }) {
  const [drawerPerson, setDrawerPerson] = useState(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const [filterState, setFilterState] = useState({
    person: '',
    eventTypes: { birth: true, death: true, residence: true },
    relations: { direct: true, siblings: false, cousins: false, inlaws: false },
    sources: { gedcom: true, census: true, manual: true, ai: true },
    year: [1900, 2000],
    vague: false,
  });

  const filteredMovements = useMemo(() => {
    return allMovements.filter((mv) => {
      const { person, year, eventTypes, vague, relations, sources } = filterState;
      const nameMatch = person.trim() === '' || mv.person_name?.toLowerCase().includes(person.toLowerCase());
      const typeMatch = eventTypes[mv.event_type?.toLowerCase()] ?? false;
      const yr = parseInt(mv.year, 10);
      const yearMatch = isNaN(yr) ? true : yr >= year[0] && yr <= year[1];
      const vagueMatch = vague || (!!mv.latitude && !!mv.longitude);
      const sourceMatch = mv.source ? sources[mv.source] ?? false : true;
      const relationMatch = true;
      return nameMatch && typeMatch && yearMatch && vagueMatch && sourceMatch && relationMatch;
    });
  }, [allMovements, filterState]);

  const handleSelectPerson = (personId) => {
    const m = allMovements.find((x) => x.person_id === personId);
    if (m) setDrawerPerson({ person_id: personId, person_name: m.person_name });
  };

  return (
    <div className="relative w-full" style={{ height: 'calc(100vh - 80px)' }}>
      {/* 🌫 GeneaGlass HUD Filter Panel */}
      <GeneaGlassPanel
        filterState={filterState}
        setFilterState={setFilterState}
        onOpenAdvanced={() => setIsFilterOpen(true)}
      />

      {/* 🧠 Advanced Filter Drawer */}
      <AdvancedFilterDrawer
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        filterState={filterState}
        setFilterState={setFilterState}
        onApply={() => setIsFilterOpen(false)}
      />

      {/* 🗺️ Map */}
      <MigrationMap
        movements={filteredMovements}
        center={mapCenter}
        onMarkerClick={handleSelectPerson}
        activePersonIds={drawerPerson ? new Set([drawerPerson.person_id]) : new Set()}
      />

      {/* 📍 Legend */}
      <Legend movements={filteredMovements} className="absolute bottom-6 left-6 z-10" />

      {/* ♻️ Reset */}
      <FloatingHUD
        selectedPersonName={drawerPerson?.person_name}
        onReset={() => setDrawerPerson(null)}
      />

      {/* 📄 Person Info */}
      {drawerPerson && (
        <PersonDrawer
          personId={drawerPerson.person_id}
          personName={drawerPerson.person_name}
          movements={filteredMovements.filter((m) => m.person_id === drawerPerson.person_id)}
          onClose={() => setDrawerPerson(null)}
        />
      )}
    </div>
  );
}
