// frontend/src/features/map/components/MapMarkers.jsx
import React from "react"
import { Marker, Popup } from "react-leaflet"
import L from "leaflet"
import { log as devLog } from "@/lib/api/devLogger.js"

const DEBUG = process.env.NODE_ENV === "development"

const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function MapMarkers({ movements = [], onClick = () => {} }) {
  return (
    <>
      {movements.map((mv) => {
        const key = mv.event_id
          ? String(mv.event_id)
          : `${mv.person_id}_${mv.event_type}_${mv.date}`

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
              {mv.date ? new Date(mv.date).getFullYear() || "?" : "?"})
            </Popup>
          </Marker>
        )
      })}
    </>
  )
}
