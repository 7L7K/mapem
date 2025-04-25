// frontend/src/features/map/pages/MapPage.jsx
import React, { useEffect, useState } from 'react';
import { useTree } from '@shared/context/TreeContext';
import { useSearch } from '@shared/context/SearchContext';
import { useMapControl } from '@shared/context/MapControlContext';
import { getMovements, getTrees } from '@lib/api/api';
import MapView from '@/features/map/components/MigrationMap';
import AdvancedFilterDrawer from '@/features/map/components/AdvancedFilterDrawer';
import TypeSearch from '@/features/map/components/TypeSearch';
import PersonSelector from '@/features/map/components/PersonSelector';
import FilterHeader from '@shared/components/Header/FilterHeader';
import LegendPanel from '@/features/map/components/LegendPanel';

export default function MapPage() {
  const { treeId, setTreeId } = useTree();
  const { filters } = useSearch();                
  const { activeSection, toggleSection } = useMapControl();
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Bootstrap a treeId on mount
  useEffect(() => {
    if (!treeId) {
      getTrees().then((trees) => trees.length && setTreeId(trees[0].id));
    }
  }, [treeId]);

  // Fetch movement data when treeId changes
  useEffect(() => {
    if (!treeId) return;
    setLoading(true);
    getMovements(treeId)
      .then((res) => {
        const flat = (res || []).flatMap((p) =>
          p.movements.map((m) => ({
            ...m,
            person_id: p.person_id,
            person_name: p.person_name,
          }))
        );
        setMovements(flat);
      })
      .catch(() => setError('Failed to load movements.'))
      .finally(() => setLoading(false));
  }, [treeId]);

  return (
    <div className="relative w-full h-full">
      {/* top control bar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 w-[90vw] max-w-4xl">
        <FilterHeader>
          {/* SEARCH */}
          {activeSection === null || activeSection === 'search' ? <TypeSearch /> : null}
          {/* PERSON SELECTOR */}
          {activeSection === 'person' && <PersonSelector />}
          {/* FILTERS BUTTON */}
          {activeSection === null && (
            <button onClick={() => toggleSection('filters')} className="text-sm text-accent hover:underline">
              Filters
            </button>
          )}
        </FilterHeader>
      </div>

      {/* drawer renders when activeSection==='filters' via context */}
      {activeSection === 'filters' && <AdvancedFilterDrawer />}

      {/* main map rendering */}
      <MapView movements={movements} loading={loading} error={error} />

      {/* legend panel */}
      <LegendPanel />
    </div>
  );
}
