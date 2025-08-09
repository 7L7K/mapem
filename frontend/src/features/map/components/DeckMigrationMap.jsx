import React, { useMemo, useRef, useEffect, useState } from "react";
import DeckGL from "@deck.gl/react";
import { Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer, ArcLayer, TextLayer, GeoJsonLayer } from "@deck.gl/layers";

const DEFAULT_STYLE = "https://demotiles.maplibre.org/style.json";

export default function DeckMigrationMap({ movements = [], onSelect = () => { }, year }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const overlayRef = useRef(null);
  const [viewState, setViewState] = useState({
    longitude: -96,
    latitude: 37.8,
    zoom: 3.5,
    pitch: 0,
    bearing: 0,
  });

  const firstPoint = useMemo(() => {
    for (const mv of movements) {
      const lat = mv.latitude ?? mv._markerLat ?? mv?.from?.lat;
      const lng = mv.longitude ?? mv._markerLng ?? mv?.from?.lng;
      if (typeof lat === "number" && typeof lng === "number") return { lat, lng };
    }
    return null;
  }, [movements]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: DEFAULT_STYLE,
      center: [viewState.longitude, viewState.latitude],
      zoom: viewState.zoom,
      attributionControl: true,
    });
    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    map.addControl(overlay);
    map.on("move", () => {
      const c = map.getCenter();
      setViewState((s) => ({
        ...s,
        longitude: c.lng,
        latitude: c.lat,
        zoom: map.getZoom(),
        bearing: map.getBearing(),
        pitch: map.getPitch(),
      }));
    });
    mapRef.current = map;
    overlayRef.current = overlay;
  }, []);

  useEffect(() => {
    if (firstPoint && mapRef.current) {
      mapRef.current.jumpTo({ center: [firstPoint.lng, firstPoint.lat], zoom: 4 });
    }
  }, [firstPoint]);

  const [borders, setBorders] = useState(null);
  useEffect(() => {
    let aborted = false;
    (async () => {
      try {
        const params = new URLSearchParams();
        if (year) params.set('year', String(year));
        const res = await fetch(`/api/heatmap?${params.toString()}`);
        if (!res.ok) return;
        const json = await res.json();
        if (!aborted) {
          setBorders({ type: 'FeatureCollection', features: json.shapes || [] });
        }
      } catch { }
    })();
    return () => { aborted = true; };
  }, [year]);

  const isSegment = (mv) => mv && mv.from && mv.to;

  const layers = useMemo(() => {
    const pointData = movements
      .filter((m) => !isSegment(m))
      .map((m) => ({
        position: [m.longitude ?? m._markerLng, m.latitude ?? m._markerLat],
        person_id: m.person_id,
        event_type: m.event_type,
        name: Array.isArray(m.names) ? m.names[0] : m.name,
        year: m.date ? new Date(m.date).getFullYear() : undefined,
      }))
      .filter(
        (d) =>
          Array.isArray(d.position) &&
          Number.isFinite(d.position[0]) &&
          Number.isFinite(d.position[1])
      );

    const scatter = new ScatterplotLayer({
      id: "residences",
      data: pointData,
      getPosition: (d) => d.position,
      getFillColor: [255, 180, 0],
      getRadius: 40,
      radiusUnits: "pixels",
      pickable: true,
      autoHighlight: true,
      onClick: (info) => info?.object && onSelect({ type: "point", data: info.object }),
    });

    const segments = movements.filter((m) => isSegment(m));
    const arcs = new ArcLayer({
      id: "migrations",
      data: segments,
      getSourcePosition: (d) => [d.from.lng, d.from.lat],
      getTargetPosition: (d) => [d.to.lng, d.to.lat],
      getSourceColor: (d) => {
        if (d.impossible) return [154, 160, 166, 140]; // gray
        if (d.suspicious) return [255, 77, 79]; // red
        if ((d.confidence_score ?? 1) < 0.5) return [255, 176, 32]; // orange
        return [72, 187, 255];
      },
      getTargetColor: (d) => {
        if (d.impossible) return [154, 160, 166, 140];
        if (d.suspicious) return [255, 77, 79];
        if ((d.confidence_score ?? 1) < 0.5) return [255, 176, 32];
        return [72, 187, 255];
      },
      getWidth: (d) => (d.suspicious ? 3 : 2),
      pickable: true,
      greatCircle: true,
      onClick: (info) => info?.object && onSelect({ type: "arc", data: info.object }),
    });

    const labels = new TextLayer({
      id: "labels",
      data: pointData,
      getPosition: (d) => d.position,
      getText: (d) => (d.name ? String(d.name) : ""),
      getSize: 12,
      getColor: [230, 230, 230],
      getTextAnchor: "start",
      getAlignmentBaseline: "center",
      maxWidth: 200,
      characterSet: "auto",
    });

    const borderLayer = borders && new GeoJsonLayer({
      id: 'borders',
      data: borders,
      stroked: true,
      filled: false,
      getLineColor: [136, 136, 136, 180],
      getLineWidth: 1,
      lineWidthUnits: 'pixels',
      pickable: false,
    });

    return [borderLayer, arcs, scatter, labels].filter(Boolean);
  }, [movements, onSelect, borders]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="absolute inset-0" />
      <DeckGL
        viewState={viewState}
        controller={true}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        layers={layers}
        getTooltip={({ object }) => {
          if (!object) return null;
          if (object.from && object.to) {
            const y0 = object.from?.date ? new Date(object.from.date).getFullYear() : "?";
            const y1 = object.to?.date ? new Date(object.to.date).getFullYear() : "?";
            return { text: `${y0} → ${y1} (${object.event_type || "move"})` };
          }
          const y = object.year ?? "?";
          return { text: `${object.name || "Event"} (${y})` };
        }}
      />
    </div>
  );
}


