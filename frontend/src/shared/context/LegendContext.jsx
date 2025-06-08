// frontend/src/shared/context/LegendContext.jsx
import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import { useSearch } from "@shared/context/SearchContext";
import { useTree } from "@shared/context/TreeContext";
import * as api from "@lib/api/api";
import { devLog } from "@shared/utils/devLogger";

const LegendContext = createContext(null);
export const useLegend = () => useContext(LegendContext);

export function LegendProvider({ children }) {
  const { filters, mode } = useSearch();
  const { treeId } = useTree();
  const [counts, setCounts] = useState({
    people: 0,
    families: 0,
    household: 0,
    wholeTree: 0,
    relatives: {},
  });

  // 1) Whole-tree totals
  useEffect(() => {
    if (!treeId) return;
    devLog("LegendContext", "📊 Fetching whole-tree counts for", { treeId });
    api.getTreeCounts(treeId)
      .then((res) => {
        devLog("LegendContext", "✅ Got tree counts", res);
        const people = res.people ?? res.totalPeople ?? 0;
        const families = res.families ?? res.totalFamilies ?? 0;
        setCounts((c) => ({ ...c, wholeTree: people, families }));
      })
      .catch((err) => {
        devLog("LegendContext", "❌ getTreeCounts failed", err);
      });
  }, [treeId]);

  // 2) Visible counts
  useEffect(() => {
    if (!treeId) return;
    devLog("LegendContext", "🔍 Fetching visible counts for", { mode, filters });
    api.getVisibleCounts(treeId, filters)
    .then((res) => {
      devLog("LegendContext", "✅ Got visible counts", res);
      const people = res.people ?? 0;
      const families = res.families ?? 0;
      setCounts((c) => ({ ...c, people, families }));
    })
        .catch((err) => devLog("LegendContext", "❌ getVisibleCounts failed", err));
  }, [treeId, filters, mode]);

  // 3) Household size
  useEffect(() => {
    const pid = filters.selectedPersonId;
    if (!pid) return;
    devLog("LegendContext", "👥 Fetching household size for", { personId: pid });
    api.getHousehold(pid, filters.yearRange[1])
      .then((list) => {
        devLog("LegendContext", "✅ Got household list", list);
        setCounts((c) => ({ ...c, household: list.length }));
      })
      .catch((err) => devLog("LegendContext", "❌ getHousehold failed", err));
  }, [filters.selectedPersonId, filters.yearRange]);

  // 4) Relatives
  useEffect(() => {
    const pid = filters.selectedPersonId;
    if (!pid) return;
    const types = Object.keys(filters.relations).filter((k) => filters.relations[k]);
    devLog("LegendContext", "📡 Fetching relatives for", { personId: pid, types });
    api.getRelatives(pid, types)
      .then((rel) => {
        devLog("LegendContext", "✅ Got relatives", rel);
        setCounts((c) => ({ ...c, relatives: rel }));
      })
      .catch((err) => devLog("LegendContext", "❌ getRelatives failed", err));
  }, [filters.selectedPersonId, filters.relations]);

  const value = useMemo(() => ({ counts }), [counts]);
  return <LegendContext.Provider value={value}>{children}</LegendContext.Provider>;
}
