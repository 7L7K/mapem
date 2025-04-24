// frontend/src/features/map/pages/MapPage.jsx
import React, { useEffect, useState } from "react";
import { useTree } from "@shared/context/TreeContext";
import { useSearch } from "@shared/context/SearchContext";
import { getMovements, getTrees } from "@lib/api/api";
import MapView from "@/features/map/components/MigrationMap";
import AdvancedFilterDrawer from "@/features/map/components/AdvancedFilterDrawer";
import QuickFilterBar from "@/features/map/components/QuickFilterBar";
import FloatingFilterPill from "@shared/components/MapHUD/FloatingFilterPill";


export default function MapPage() {
  const { treeId, setTreeId } = useTree();
  const { isDrawerOpen, setIsDrawerOpen } = useSearch();
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!treeId) {
      getTrees().then((trees) => {
        if (trees.length > 0) setTreeId(trees[0].id);
      });
    }
  }, [treeId]);

  useEffect(() => {
    if (!treeId) return;
    setLoading(true);
    getMovements(treeId)
      .then((res) => {
        setMovements(
          (res || []).flatMap((p) =>
            p.movements.map((m) => ({
              ...m,
              person_id: p.person_id,
              person_name: p.person_name,
            }))
          )
        );
      })
      .catch(() => setError("Failed to load movements."))
      .finally(() => setLoading(false));
  }, [treeId]);

  return (
    <div className="relative w-full h-full">
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40">
        <QuickFilterBar />
      </div>

      {/* Map */}
      <MapView movements={movements} loading={loading} error={error} />

      {/* Filters */}
      <FloatingFilterPill />
      <AdvancedFilterDrawer />
    </div>
  );
}
