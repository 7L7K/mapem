import React from "react";
import { Card } from "@shared/components/ui/Card";

export default function Legend({ movements = [], people = 0, families = 0, className = "" }) {
  const eventTypes = Array.from(new Set(movements.map((m) => m.event_type)));

  return (
    <Card className={`p-4 ${className}`}>
      <h3 className="text-sm font-semibold mb-2">Legend</h3>

      {/* 🔥 Add People/Families */}
      <ul className="space-y-1 text-sm text-dim mb-2">
        <li>👤 People: {people}</li>
        <li>🏡 Families: {families}</li>
      </ul>

      <h4 className="text-xs font-semibold mt-3 mb-1 text-muted">Event Types:</h4>
      <ul className="space-y-1 text-sm text-dim">
        {eventTypes.map((type) => (
          <li key={type}>• {type}</li>
        ))}
      </ul>
    </Card>
  );
}
