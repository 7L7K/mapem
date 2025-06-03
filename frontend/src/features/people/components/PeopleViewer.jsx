import React, { useEffect, useState } from "react";
import { FixedSizeList as List } from "react-window";
import * as api from "@lib/api/api";
import { useTree } from "@shared/context/TreeContext";

/**
 * Virtualised list of Individuals for the active tree.
 * Currently grabs the first 500 rows—pagination coming later.
 */
export default function PeopleViewer() {
  const { treeId } = useTree();
  const [people, setPeople] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (!treeId) return;

    api
      .getPeople(treeId, 500, 0)
      .then(({ people, total }) => {
        setPeople(people);
        setTotal(total);
        console.debug("[PeopleViewer] loaded", people.length, "of", total);
      })
      .catch((err) => console.error("[PeopleViewer] fetch failed", err));
  }, [treeId]);

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
      <h2 className="text-lg mb-2">
        👥 People ({people.length}/{total})
      </h2>
      <List
        height={window.innerHeight - 180}
        itemCount={people.length}
        itemSize={48}
        width={"100%"}
      >
        {Row}
      </List>
    </section>
  );
}
