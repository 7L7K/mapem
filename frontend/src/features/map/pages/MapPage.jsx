// frontend/src/features/map/pages/MapPage.jsx
import React, { useEffect, useState, useCallback } from "react"
import { useTree } from "@shared/context/TreeContext"
import { useSearch } from "@shared/context/SearchContext"
import { useMapControl } from "@shared/context/MapControlContext"
import useDebounce from "@/shared/hooks/useDebounce"
import useUrlQuerySync from "@/shared/hooks/useUrlQuerySync"
import useMovements from "@/shared/hooks/useMovements"

import LegendPanel from "@/features/map/components/LegendPanel"
import MapFilters from "@/features/map/components/MapFilters"
import LoadingOverlay from "@/features/map/components/LoadingOverlay"
import PersonMap from "@/features/map/components/PersonMap"
import FamilyMap from "@/features/map/components/FamilyMap"
import GroupMap from "@/features/map/components/GroupMap"
import TimeSlider from "@shared/components/MapHUD/TimeSlider"
import ShareLinkButton from "@shared/components/MapHUD/ShareLinkButton"
import { resolveShareLink } from "@lib/api/api"
import InspectorDrawer from "@/features/map/components/InspectorDrawer"

export default function MapPage() {
  const { treeId } = useTree()
  const { filters, mode, setIsDrawerOpen, clearAll, setFilters, setMode } = useSearch()
  const { toggleSection } = useMapControl()
  const debouncedFilters = useDebounce(filters, 400)
  const { movements, loading, error } = useMovements(
    treeId,
    debouncedFilters,
    mode
  )

  const MapComponent =
    mode === "family" ? FamilyMap : mode === "compare" ? GroupMap : PersonMap

  const isEmpty = !loading && !error && movements.length === 0

  const [legendVisible, setLegendVisible] = useState(true)
  const [selection, setSelection] = useState(null)

  // Sync filters and mode with URL query params
  useUrlQuerySync(filters, setFilters, mode, setMode)

  // Apply shared-token filters from URL once
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (!token) return
      ; (async () => {
        try {
          const entry = await resolveShareLink(token)
          if (entry?.filters) setFilters(entry.filters)
        } catch { /* ignore */ }
      })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // keyboard shortcuts: F = filters, R = reset (clear filters), L = toggle legend
  const handleKey = useCallback((e) => {
    const key = e.key.toLowerCase()
    if (key === 'l') setLegendVisible(v => !v)
    if (key === 'f') { setIsDrawerOpen(true); toggleSection('filters') }
    if (key === 'r') clearAll()
  }, [setIsDrawerOpen, clearAll, toggleSection])

  useEffect(() => {
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [handleKey])

  const yearMid = Array.isArray(debouncedFilters.yearRange)
    ? Math.round((debouncedFilters.yearRange[0] + debouncedFilters.yearRange[1]) / 2)
    : undefined

  return (
    <div className="relative w-full h-full">
      <MapFilters />
      <MapComponent movements={movements} year={yearMid} onSelect={setSelection} />
      <TimeSlider />
      <ShareLinkButton />
      <LoadingOverlay loading={loading} error={error} empty={isEmpty} />
      {legendVisible && <LegendPanel />}
      <InspectorDrawer open={!!selection} onClose={() => setSelection(null)} selection={selection} />

      {/* Legend toggle */}
      <button
        onClick={() => setLegendVisible(v => !v)}
        className="absolute right-4 bottom-4 z-50 bg-black/70 text-white text-xs px-3 py-2 rounded-md border border-white/10 hover:bg-black/80"
        aria-pressed={legendVisible}
      >
        {legendVisible ? 'Hide Legend (L)' : 'Show Legend (L)'}
      </button>
    </div>
  )
}
