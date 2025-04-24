import React, { useEffect, useState } from "react";
import { useTree } from "@shared/context/TreeContext";
import { getPeople } from "@lib/api/api";
import Loader from "@shared/components/ui/Loader";
import ErrorBox from "@shared/components/ui/ErrorBox";

export default function PeopleViewer() {
  const { treeId } = useTree();
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!treeId) return;
    getPeople(treeId)
      .then((data) => {
        console.log("👥 Loaded people for tree", treeId, data);
        setPeople(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("❌ Error loading people:", err);
        setError("Failed to load people.");
      })
      .finally(() => setLoading(false));
  }, [treeId]);

  if (loading) return <Loader />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div className="p-6 space-y-4 text-white">
      <h2 className="text-2xl font-bold font-display text-white">👤 People in Tree</h2>

      {people.length === 0 ? (
        <p className="text-dim italic">No people found for this tree.</p>
      ) : (
        <ul className="space-y-2">
          {people.map((p) => (
            <li
              key={p.id}
              className="bg-surface border border-border p-4 rounded-xl shadow-sm hover:shadow-md transition-all"
            >
              <div className="font-semibold">{p.name || "Unnamed"}</div>
              <div className="text-dim text-sm">
                {p.occupation || "No occupation listed"}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
