import React, { useState, useEffect, useMemo } from "react";
import { useTree } from "../context/TreeContext";
import { getMovements } from "../services/api";

import MapView from "../components/MapView";
import AdvancedFilterDrawer from "../components/Map/AdvancedFilterDrawer";

export default function MapPage() {
  const { treeId } = useTree();

  const [filterState, setFilterState] = useState({
    person: "",
    year: [1900, 2000],
    eventTypes: {
      birth: true,
      death: true,
      residence: true,
    },
    vague: false,
    relations: {
      direct: true,
      siblings: false,
      cousins: false,
      inlaws: false,
    },
    sources: {
      gedcom: true,
      census: true,
      manual: false,
      ai: false,
    },
    view: "person",
  });

  const [isDrawerOpen, setDrawerOpen] = useState(false);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [drawerPerson, setDrawerPerson] = useState(null);

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
      .catch((err) => {
        console.error(err);
        setError("Failed to load movements.");
      })
      .finally(() => setLoading(false));
  }, [treeId]);

  const filteredMovements = useMemo(() => {
    return movements.filter((mv) => {
      const { person, year, eventTypes, vague } = filterState;
      const type = (mv.event_type || "").toLowerCase();
      const okType =
        (type.includes("birth") && eventTypes.birth) ||
        (type.includes("death") && eventTypes.death) ||
        (type.includes("residence") && eventTypes.residence);

      const yr = parseInt(mv.year, 10);
      const okYear = isNaN(yr) ? true : yr >= year[0] && yr <= year[1];

      const okPerson =
        person.trim() === "" ||
        mv.person_name.toLowerCase().includes(person.toLowerCase());

      const okVague = vague || (!!mv.latitude && !!mv.longitude);

      return okType && okYear && okPerson && okVague;
    });
  }, [movements, filterState]);

  const mapCenter = useMemo(() => {
    if (drawerPerson) {
      const personMoves = filteredMovements.filter(
        (m) => m.person_id === drawerPerson.person_id
      );
      if (personMoves.length) {
        const last = personMoves[personMoves.length - 1];
        return [last.latitude, last.longitude];
      }
    }

    if (!filteredMovements.length) return [37.8, -96];

    const avg = filteredMovements.reduce(
      (acc, m) => {
        acc.lat += m.latitude;
        acc.lng += m.longitude;
        return acc;
      },
      { lat: 0, lng: 0 }
    );
    return [
      avg.lat / filteredMovements.length,
      avg.lng / filteredMovements.length,
    ];
  }, [filteredMovements, drawerPerson]);

  const handleReset = () => setDrawerPerson(null);

  return (
    <>
      <MapView
        movements={filteredMovements}
        mapCenter={mapCenter}
        drawerPerson={drawerPerson}
        setDrawerPerson={setDrawerPerson}
        handleReset={handleReset}
        loading={loading}
        error={error}
      />

      <AdvancedFilterDrawer
        isOpen={isDrawerOpen}
        filterState={filterState}
        setFilterState={setFilterState}
        onClose={() => setDrawerOpen(false)}
        onApply={() => setDrawerOpen(false)}
      />
    </>
  );
}
