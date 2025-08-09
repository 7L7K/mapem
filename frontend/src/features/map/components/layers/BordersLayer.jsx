import React, { useEffect, useState } from "react";
import { GeoJSON, useMap } from "react-leaflet";

export default function BordersLayer({ year }) {
    const [data, setData] = useState(null);
    const map = useMap();

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const params = new URLSearchParams();
                if (year) params.set("year", String(year));
                const res = await fetch(`/api/heatmap?${params.toString()}`);
                if (!res.ok) return;
                const json = await res.json();
                if (!cancelled) {
                    setData({ type: "FeatureCollection", features: json.shapes ?? [] });
                }
            } catch (e) {
                // ignore
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, [year]);

    if (!data || !data.features?.length) return null;

    return (
        <GeoJSON
            key={`borders-${year}`}
            data={data}
            style={() => ({ color: "#888", weight: 1, fill: false, opacity: 0.6 })}
            onEachFeature={(feature, layer) => {
                const name = feature?.properties?.name || "Unknown";
                const count = feature?.properties?.count;
                const yr = feature?.properties?.year ?? year;
                const desc = `${name}${yr ? ` (${yr})` : ""}${count ? ` — ${count}` : ""}`;
                layer.bindTooltip(desc);
            }}
        />
    );
}


