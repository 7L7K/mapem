// frontend/src/features/map/pages/MapPage.jsx
import React from "react"
import { useTree } from "@shared/context/TreeContext"
import { useSearch } from "@shared/context/SearchContext"
import useDebounce from "@/shared/hooks/useDebounce"
import useMovements from "@/shared/hooks/useMovements"

import LegendPanel from "@/features/map/components/LegendPanel"
import MapFilters from "@/features/map/components/MapFilters"
import LoadingOverlay from "@/features/map/components/LoadingOverlay"
import PersonMap from "@/features/map/components/PersonMap"
import FamilyMap from "@/features/map/components/FamilyMap"
import GroupMap from "@/features/map/components/GroupMap"

export default function MapPage() {
  const { treeId } = useTree()
  const { filters, mode } = useSearch()
  const debouncedFilters = useDebounce(filters, 400)
  const { movements, loading, error } = useMovements(
    treeId,
    debouncedFilters,
    mode
  )

  const MapComponent =
    mode === "family" ? FamilyMap : mode === "compare" ? GroupMap : PersonMap

  const isEmpty = !loading && !error && movements.length === 0

  return (
    <div className="relative w-full h-full">
      <MapFilters />
      <MapComponent movements={movements} />
      <LoadingOverlay loading={loading} error={error} empty={isEmpty} />
      <LegendPanel />
    </div>
  )
}
