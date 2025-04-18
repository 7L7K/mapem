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

import "../styles/MapView.postcss";
import MigrationMapBoundary from './Map/MigrationMapBoundary';

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
    log("🔄 [MapView] filterState changed:", filterState);
  }, [filterState]);

  // fetch movements
  const [movements, setMovements] = useState([]);
  useEffect(() => {
    if (!treeId) return;
    setLoading(true);
    setError(null);
    log(`📡 [MapView] fetching movements for treeId=${treeId}`);
    getMovements(treeId)
      .then(res => {
        const flat = (res || []).flatMap(p =>
          p.movements.map(m => ({ ...m, person_id: p.person_id, person_name: p.person_name }))
        );
        log('✅ [MapView] loaded', flat.length, 'total events');
        setMovements(flat);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load movement data.');
      })
      .finally(() => setLoading(false));
  }, [treeId]);

  // apply filters
  const [filteredMovements, setFilteredMovements] = useState([]);
  const applyFilters = useCallback(() => {
    log('🔍 [MapView] applying filters to', movements.length, 'movements');
    const result = movements.filter(mv => {
      const { person, year, eventTypes, vague } = filterState;
      // type
      const t = (mv.event_type || '').toLowerCase();
      const okType =
        (t.includes('birth') && eventTypes.birth) ||
        (t.includes('death') && eventTypes.death) ||
        (t.includes('residence') && eventTypes.residence);
      // year
      const yr = parseInt(mv.year,10);
      const okYear = isNaN(yr) ? true : yr >= year[0] && yr <= year[1];
      // person
      const okPerson = person.trim() === '' ||
        mv.person_name.toLowerCase().includes(person.toLowerCase());
      // vague
      const okVague = vague || (!!mv.latitude && !!mv.longitude);
      return okType && okYear && okPerson && okVague;
    });
    log('✅ [MapView] filter result count:', result.length);
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
        acc.lat += m.latitude; acc.lng += m.longitude; return acc;
      },
      { lat: 0, lng: 0 }
    );
    return [avg.lat / filteredMovements.length, avg.lng / filteredMovements.length];
  }, [filteredMovements]);
  log('🔭 [MapView] mapCenter:', mapCenter);

// …everything above stays the same …

  return (
    <div className="map-view-container mt-20">   {/* 20 = 5rem; tweak if needed */}
      {/* Filter bar + drawer sit just inside MapView, not fixed */}
      <div className="relative z-10">
        <QuickFilterBar
          filterState={filterState}
          setFilterState={setFilterState}
          onToggleDrawer={() => setDrawerOpen(true)}
        />

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
      </div>

      {/* Map & legend */}
      <div className="map-container">
        {loading && <Loader />}
        {error && <ErrorBox message={error} />}
        {!loading && !error && (
          <MigrationMapBoundary>
            <MigrationMap
              movements={filteredMovements}
              center={mapCenter}
              onMarkerClick={setDrawerPerson}
              activePersonIds={activePersonIds}
            />
            <Legend movements={filteredMovements} />
          </MigrationMapBoundary>
        )}
      </div>

      {/* Person side‑drawer */}
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
