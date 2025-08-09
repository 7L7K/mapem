import React, { useMemo, useRef, useState } from "react";
import { FixedSizeList as List } from "react-window";
import * as api from "@lib/api/api";
import { useQuery } from "@tanstack/react-query";
import { useTree } from "@shared/context/TreeContext";

/**
 * Virtualised list of Individuals for the active tree.
 * Currently grabs the first 500 rows—pagination coming later.
 */
export default function PeopleViewer() {
  const { treeId } = useTree();
  const [people, setPeople] = useState([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 100;
  const listRef = useRef(null);

  const { isLoading, error } = useQuery({
    queryKey: ["people", treeId, page, pageSize],
    queryFn: async () => {
      if (!treeId) return { people: [], total: 0 };
      return await api.getPeople(treeId, pageSize, page * pageSize);
    },
    enabled: !!treeId,
    keepPreviousData: true,
    onSuccess: ({ people, total }) => {
      setPeople(people);
      setTotal(total);
    }
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return people;
    return people.filter((p) => (p.name || "").toLowerCase().includes(q));
  }, [people, query]);

  const Row = ({ index, style }) => {
    const p = people[index];
    if (!p) return <div style={style}>…</div>;

    return (
      <div style={style} className="px-2 py-1 border-b border-[var(--border)]">
        <div className="font-medium">{p.name}</div>
        <div className="text-xs opacity-70">{p.occupation}</div>
      </div>
    );
  };

  return (
    <section className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2 gap-2">
        <h2 className="text-lg">👥 People ({filtered.length}/{total})</h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search names…"
          className="px-3 py-1 rounded-md bg-surface border border-border text-sm"
          aria-label="Search people"
        />
      </div>
      <div className="flex-1 min-h-0">
        {isLoading && <div className="p-2 text-sm opacity-70">Loading…</div>}
        {error && <div className="p-2 text-sm text-red-500">Failed to load</div>}
        <List
          ref={listRef}
          height={Math.max(240, (typeof window !== 'undefined' ? window.innerHeight : 600) - 220)}
          itemCount={filtered.length}
          itemSize={48}
          width={"100%"}
        >
          {({ index, style }) => <Row index={index} style={style} />}
        </List>
      </div>
      <div className="mt-2 flex items-center justify-end gap-2">
        <button className="px-2 py-1 rounded border border-border text-sm disabled:opacity-50" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Prev</button>
        <span className="text-xs opacity-70">Page {page + 1}</span>
        <button className="px-2 py-1 rounded border border-border text-sm disabled:opacity-50" disabled={(page + 1) * pageSize >= total} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </section>
  );
}
