// frontend/src/shared/context/LegendContext.jsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useMemo,
} from "react";
import { useSearch } from "@shared/context/SearchContext";
import { useTree } from "@shared/context/TreeContext";
import * as api from "@lib/api/api";
import { devLog } from "@shared/utils/devLogger";
import { diff } from "deep-diff";

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

  const prevRef = useRef(counts);

  // log diffs on counts changes
  useEffect(() => {
    const prev = prevRef.current;
    const changes = diff(prev, counts);
    if (changes?.length) {
      const ts = new Date().toLocaleTimeString();
      console.group(`🔖 LegendContext counts diff @${ts}`);
      changes.forEach(c => console.log("%c" + JSON.stringify(c), "color:#32CD32"));
      console.groupEnd();
    }
    prevRef.current = counts;
  }, [counts]);

  // whole-tree totals
  useEffect(() => {
    if (!treeId) return;
    const reqId = Math.random().toString(36).slice(2);
    devLog("LegendContext", `📊 [${reqId}] Fetching whole-tree counts for`, { treeId });
    api
      .getTreeCounts(treeId)
      .then(res => {
        devLog("LegendContext", `✅ [${reqId}] Got tree counts`, res);
        const people = res.people ?? res.totalPeople ?? 0;
        const families = res.families ?? res.totalFamilies ?? 0;
        setCounts(c => ({ ...c, wholeTree: people, families }));
      })
      .catch(err => devLog("LegendContext", `❌ [${reqId}] getTreeCounts failed`, err));
  }, [treeId]);

  // visible counts
  useEffect(() => {
    if (!treeId) return;
    const reqId = Math.random().toString(36).slice(2);
    devLog("LegendContext", `🔍 [${reqId}] Fetching visible counts`, {
      treeId,
      mode,
      filters,
    });
    api
      .getVisibleCounts(treeId, filters)
      .then(res => {
        devLog("LegendContext", `✅ [${reqId}] Got visible counts`, res);
        const people = res.people ?? 0;
        const families = res.families ?? 0;
        setCounts(c => ({ ...c, people, families }));
      })
      .catch(err =>
        devLog("LegendContext", `❌ [${reqId}] getVisibleCounts failed`, err)
      );
  }, [treeId, filters, mode]);

  // household size
  useEffect(() => {
    const pid = filters.selectedPersonId;
    if (!pid) return;
    const reqId = Math.random().toString(36).slice(2);
    devLog("LegendContext", `👥 [${reqId}] Fetching household size for`, {
      personId: pid,
      year: filters.yearRange[1],
    });
    api
      .getHousehold(pid, filters.yearRange[1])
      .then(list => {
        devLog("LegendContext", `✅ [${reqId}] Got household list`, list);
        setCounts(c => ({ ...c, household: list.length }));
      })
      .catch(err =>
        devLog("LegendContext", `❌ [${reqId}] getHousehold failed`, err)
      );
  }, [filters.selectedPersonId, filters.yearRange]);

  // relatives
  useEffect(() => {
    const pid = filters.selectedPersonId;
    if (!pid) return;
    const types = Object.keys(filters.relations).filter(k => filters.relations[k]);
    const reqId = Math.random().toString(36).slice(2);
    devLog("LegendContext", `📡 [${reqId}] Fetching relatives for`, {
      personId: pid,
      types,
    });
    api
      .getRelatives(pid, types)
      .then(rel => {
        devLog("LegendContext", `✅ [${reqId}] Got relatives`, rel);
        setCounts(c => ({ ...c, relatives: rel }));
      })
      .catch(err =>
        devLog("LegendContext", `❌ [${reqId}] getRelatives failed`, err)
      );
  }, [filters.selectedPersonId, filters.relations]);

  const value = useMemo(() => ({ counts }), [counts]);
  return <LegendContext.Provider value={value}>{children}</LegendContext.Provider>;
}
