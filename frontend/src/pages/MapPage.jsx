import React, { useEffect, useState } from "react";
import { useTree } from "../context/TreeContext";
import { getMovements } from "../services/api";
import MapView from "../components/MapView";
import AdvancedFilterDrawer from "../components/Map/AdvancedFilterDrawer";
import { useSearch } from "/context/SearchContext";

export default function MapPage() {
  const { treeId } = useTree();
  const { showFilters, toggleFilters } = useSearch();

  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!treeId) return;
    setLoading(true);
    getMovements(treeId)
      .then(res => {
        setMovements((res || []).flatMap(p => p.movements.map(m => ({
          ...m,
          person_id: p.person_id,
          person_name: p.person_name,
        }))));
      })
      .catch(err => setError("Failed to load movements."))
      .finally(() => setLoading(false));
  }, [treeId]);

  return (
    <>
      <MapView movements={movements} loading={loading} error={error} />
      <AdvancedFilterDrawer
        isOpen={showFilters}
        onClose={toggleFilters}
        onApply={toggleFilters}
      />
    </>
  );
}
