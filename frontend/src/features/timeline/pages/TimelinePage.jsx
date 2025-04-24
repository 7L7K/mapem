// TimelinePage.jsx
import React from "react";

export default function TimelinePage() {
  return (
    <section className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center text-center">
      <h1 className="text-3xl font-display mb-4">📅 Timeline (WIP)</h1>
      <p className="text-white/70 max-w-md">
        This will visualize life-event timelines for selected people or families.
        <br />
        Coming soon – filters, zoom, and synced map playback.
      </p>
    </section>
  );
}
