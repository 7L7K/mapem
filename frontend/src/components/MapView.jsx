///Users/kingal/mapem/frontend/src/components/MapView.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTree } from '../context/TreeContext';
import { getMovements } from '../services/api';

import QuickFilterBar from './Map/QuickFilterBar';
import AdvancedFilterDrawer from './Map/AdvancedFilterDrawer';
import MigrationMap from './Map/MigrationMap';
import Legend from './Map/Legend';
import PersonDrawer from './Map/PersonDrawer';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import MigrationMapBoundary from './Map/MigrationMapBoundary';

import '../styles/MapView.postcss';

const log = (...args) => console.log('🗺️ [MapView]', ...args);

const MapView = () => {
  const { treeId } = useTree();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [drawerPerson, setDrawerPerson] = useState(null);
  const [isDrawerOpen, setDrawerOpen] = useState(false);

  const [filterState, setFilterState] = useState({
    person: '',
    year: [1900, 2000],
    eventTypes: { birth: true, death: true, residence: true },
    vague: false,
    relations: { direct: true, siblings: false, cousins: false, inlaws: false },
    sources: { gedcom: true, census: true, manual: false, ai: false },
    view: 'person'
  });

  useEffect(() => {
    log("🔄 filterState changed:", filterState);
  }, [filterState]);

  const [movements, setMovements] = useState([]);
  useEffect(() => {
    if (!treeId) return;
    setLoading(true);
    setError(null);
    log(`📡 fetching movements for treeId=${treeId}`);
    getMovements(treeId)
      .then(res => {
        const flat = (res || []).flatMap(p =>
          p.movements.map(m => ({ ...m, person_id: p.person_id, person_name: p.person_name }))
        );
        log('✅ loaded', flat.length, 'total events');
        setMovements(flat);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load movement data.');
      })
      .finally(() => setLoading(false));
  }, [treeId]);

  const [filteredMovements, setFilteredMovements] = useState([]);
  const applyFilters = useCallback(() => {
    log('🔍 applying filters to', movements.length, 'movements');
    const result = movements.filter(mv => {
      const { person, year, eventTypes, vague } = filterState;
      const t = (mv.event_type || '').toLowerCase();
      const okType =
        (t.includes('birth') && eventTypes.birth) ||
        (t.includes('death') && eventTypes.death) ||
        (t.includes('residence') && eventTypes.residence);
      const yr = parseInt(mv.year, 10);
      const okYear = isNaN(yr) ? true : yr >= year[0] && yr <= year[1];
      const okPerson = person.trim() === '' ||
        mv.person_name.toLowerCase().includes(person.toLowerCase());
      const okVague = vague || (!!mv.latitude && !!mv.longitude);
      return okType && okYear && okPerson && okVague;
    });
    log('✅ filter result count:', result.length);
    setFilteredMovements(result);
  }, [movements, filterState]);
  useEffect(applyFilters, [applyFilters]);

  const activePersonIds = useMemo(
    () => new Set(filteredMovements.map(m => m.person_id)),
    [filteredMovements]
  );

  const mapCenter = useMemo(() => {
    if (!filteredMovements.length) return [37.8, -96];
    const avg = filteredMovements.reduce(
      (acc, m) => {
        acc.lat += m.latitude;
        acc.lng += m.longitude;
        return acc;
      },
      { lat: 0, lng: 0 }
    );
    const center = [avg.lat / filteredMovements.length, avg.lng / filteredMovements.length];
    log('📍 mapCenter:', center);
    return center;
  }, [filteredMovements]);

  // 👀 MapView render log
  useEffect(() => {
    const el = document.querySelector('#map-debug-container');
    if (el) {
      const rect = el.getBoundingClientRect();
      console.log('%c[MapView] Map container height:', 'color:magenta', rect.height);
    } else {
      console.warn('%c[MapView] #map-debug-container not found', 'color:red');
    }
  }, [filteredMovements]);

  return (
    <div className="flex h-[calc(100vh-5rem)] mt-20 overflow-hidden bg-neutral-900">
      {/* Left Panel (Sidebar) */}
      <div className="w-[300px] text-white p-2 border-r border-neutral-800 overflow-y-auto bg-neutral-900">
        <QuickFilterBar
          filterState={filterState}
          setFilterState={setFilterState}
          onToggleDrawer={() => setDrawerOpen(true)}
        />
      </div>

      {/* Main Map Area */}
      <div className="flex-1 flex flex-col bg-transparent h-full min-h-[600px] relative">
        <AdvancedFilterDrawer
          isOpen={isDrawerOpen}
          filterState={filterState}
          setFilterState={setFilterState}
          onClose={() => setDrawerOpen(false)}
          onApply={() => {
            applyFilters();
            setDrawerOpen(false);
          }}
        />

        {/* Map + Loader/Error */}
        <div
          id="map-debug-container"
          className="relative w-full z-0 border-4 border-red-500"
          style={{
            height: 'calc(100vh - 100px)',
            minHeight: '600px',
          }}
        >
          {loading && <Loader />}
          {error && <ErrorBox message={error} />}
          {!loading && !error && filteredMovements.length > 0 && (
            <MigrationMapBoundary>
                <MigrationMap
                  movements={filteredMovements}
                  center={mapCenter}
                  onMarkerClick={setDrawerPerson}
                  activePersonIds={activePersonIds}
                />
            </MigrationMapBoundary>
          )}
        </div>
      </div>

      {/* Person Info Drawer */}
      <PersonDrawer
        personId={drawerPerson?.person_id}
        personName={drawerPerson?.person_name}
        movements={
          drawerPerson
            ? movements.filter((m) => m.person_id === drawerPerson.person_id)
            : []
        }
        onClose={() => setDrawerPerson(null)}
      />
    </div>
  );
};

export default MapView;
