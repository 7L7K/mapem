import React, { useEffect, useState, useCallback } from "react"
import {
  getMovements,
  getFamilyMovements,
  getGroupMovements,
} from "@lib/api/api"
import { useTree }  from "@shared/context/TreeContext"
import { useSearch } from "@shared/context/SearchContext"
import LegendPanel     from "@/features/map/components/LegendPanel"
import MapFilters      from "@/features/map/components/MapFilters"
import LoadingOverlay  from "@/features/map/components/LoadingOverlay"
import PersonMap       from "@/features/map/components/PersonMap"
import FamilyMap       from "@/features/map/components/FamilyMap"
import GroupMap        from "@/features/map/components/GroupMap"
import { log as devLog } from "@/lib/api/devLogger.js"


export default function MapPage() {
  const { treeId } = useTree()
  const { filters, mode } = useSearch()

  const [movements, setMovements] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const MapComponent =
    mode === "family" ? FamilyMap : mode === "compare" ? GroupMap : PersonMap

  // tree selection handled by TreeProvider

  const fetchMovements = useCallback(() => {
    if (!treeId) return

    setLoading(true)
    setError(null)
    devLog("MapPage", "🗺️ fetching movements", { treeId, filters, mode })

    const { selectedFamilyId, compareIds, ...baseFilters } = filters

    const fetcher =
      mode === "family"
        ? getFamilyMovements(treeId, selectedFamilyId, baseFilters)
        : mode === "compare"
        ? getGroupMovements(treeId, compareIds, baseFilters)
        : getMovements(treeId, baseFilters)

    fetcher
      .then(data => {
        let segments = []
        if (Array.isArray(data) && data.length && data[0].event_type) {
          segments = data
        } else if (Array.isArray(data)) {
          segments = data.flatMap(person =>
            (person.movements || []).map(m => ({
              ...m,
              person_id: person.person_id,
              person_name: person.name,
            }))
          )
        }
        setMovements(segments)
      })
      .catch(err => {
        console.error("❌ Movement fetch failed", err)
        devLog("MapPage", `❌ movement fetch error`, err)
        setError("Failed to load movements.")
      })
      .finally(() => {
        setLoading(false)
        devLog("MapPage", "✅ done fetching movements")
      })
  }, [treeId, filters, mode])

  useEffect(() => {
    fetchMovements()
  }, [fetchMovements])

  useEffect(() => {
    if (!loading && !error && movements.length === 0) {
      devLog('MapPage', 'ℹ️ no movements found')
    }
  }, [loading, error, movements.length])

  return (
    <div className="relative w-full h-full">
      <MapFilters />
      <MapComponent movements={movements} />
      <LoadingOverlay
        loading={loading}
        error={error}
        empty={!loading && !error && movements.length === 0}
      />
      <LegendPanel />
    </div>
  )
}
