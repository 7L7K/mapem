import React, { useMemo } from "react";
import { Polyline } from "react-leaflet";

// Accepts movements either as flat pins or precomputed segments.
// If an item has a "from" and "to", we render an arc-like polyline.
// Color code by suspicious speed (>= 2000 km/year).

function isSegment(item) {
    return item && item.from && item.to && typeof item.from.lat === "number" && typeof item.to.lat === "number";
}

export default function ArcsLayer({ segments = [] }) {
    const arcs = useMemo(() => {
        return segments
            .filter(isSegment)
            .map((s, idx) => {
                const from = [Number(s.from.lat), Number(s.from.lng)];
                const to = [Number(s.to.lat), Number(s.to.lng)];
                const suspicious = typeof s.speed_km_per_year === "number" && s.speed_km_per_year >= 2000;
                const impossible = !!s.impossible;
                const conf = typeof s.confidence_score === "number" ? s.confidence_score : 1.0;
                let color = "#4fb4ff";
                if (impossible) color = "#9aa0a6"; // gray
                else if (suspicious) color = "#ff4d4f"; // red
                else if (conf < 0.5) color = "#ffb020"; // orange for low confidence
                const weight = suspicious ? 3 : 2;
                const dashArray = impossible ? "6 6" : conf < 0.5 ? "2 6" : null;
                const opacity = impossible ? 0.35 : 0.75;
                return { id: `arc-${idx}`, from, to, color, weight, dashArray, opacity, s };
            });
    }, [segments]);

    if (!arcs.length) return null;

    return (
        <>
            {arcs.map((a) => (
                <Polyline
                    key={a.id}
                    positions={[a.from, a.to]}
                    pathOptions={{ color: a.color, weight: a.weight, opacity: a.opacity, dashArray: a.dashArray || undefined }}
                />)
            )}
        </>
    );
}


