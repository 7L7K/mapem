// frontend/src/features/map/components/MapMarkers.jsx
import React from "react"
import { Marker, Popup } from "react-leaflet"
import MarkerClusterGroup from 'react-leaflet-cluster'
import L from "leaflet"
import { log as devLog } from "@/lib/api/devLogger.js"

const DEBUG = process.env.NODE_ENV === "development"

const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function MapMarkers({ movements = [], onClick = () => { } }) {
  return (
    <MarkerClusterGroup chunkedLoading showCoverageOnHover={false} maxClusterRadius={50}>
      {movements.map((mv) => {
        const key = mv.event_id
          ? String(mv.event_id)
          : `${mv.person_id || mv.person_ids?.[0]}_${mv.event_type}_${mv.date || mv.to?.date}`

        return (
          <Marker
            key={key}
            position={[mv._markerLat, mv._markerLng]}
            icon={defaultIcon}
            eventHandlers={{
              click: () => {
                DEBUG && devLog("MapMarkers", "📍 clicked", mv)
                onClick(mv.person_id)
              },
            }}
          >
            <Popup>
              <strong>
                {Array.isArray(mv.names) && mv.names.length
                  ? mv.names[0]
                  : "Unknown"}
              </strong>
              <br />
              {mv.event_type} (
              {mv.date ? new Date(mv.date).getFullYear() || "?" : (mv.to?.date ? new Date(mv.to.date).getFullYear() || "?" : "?")})
              {typeof mv.speed_km_per_year === 'number' && (
                <>
                  <br />
                  Speed: {mv.speed_km_per_year.toFixed(0)} km/yr
                </>
              )}
            </Popup>
          </Marker>
        )
      })}
    </MarkerClusterGroup>
  )
}
