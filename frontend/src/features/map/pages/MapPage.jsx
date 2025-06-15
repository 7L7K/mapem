import React, { useEffect, useState } from "react"
import {
  getMovements,
  getFamilyMovements,
  getGroupMovements,
} from "@lib/api/api"
import { useTree }  from "@shared/context/TreeContext"
import { useSearch } from "@shared/context/SearchContext"
import { useMapControl } from "@shared/context/MapControlContext"
import ModeSelector    from "@shared/components/Header/ModeSelector"
import FilterHeader    from "@shared/components/Header/FilterHeader"
import AdvancedFilterDrawer from "@/features/map/components/AdvancedFilterDrawer"
import LegendPanel     from "@/features/map/components/LegendPanel"
import TypeSearch      from "@/features/map/components/TypeSearch"
import PersonSelector  from "@/features/map/components/PersonSelector"
import FamilySelector  from "@/features/map/components/FamilySelector"
import GroupSelector   from "@/features/map/components/GroupSelector"
import PersonMap       from "@/features/map/components/PersonMap"
import FamilyMap       from "@/features/map/components/FamilyMap"
import GroupMap        from "@/features/map/components/GroupMap"
import { log as devLog } from "@/lib/api/devLogger.js"


export default function MapPage() {
  const { treeId } = useTree()
  const { filters, mode } = useSearch()
  const { activeSection, toggleSection } = useMapControl()

  const [movements, setMovements] = useState([])
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const MapComponent =
    mode === "family" ? FamilyMap : mode === "compare" ? GroupMap : PersonMap

  // tree selection handled by TreeProvider

  // 📦 fetch movements when tree or filters change
  useEffect(() => {
    if (!treeId) return

    setLoading(true)
    setError(null)
    devLog("[🗺️ Fetching movements]", treeId, filters, mode)

    const { selectedFamilyId, compareIds, ...baseFilters } = filters

    const fetcher =
      mode === "family"
        ? getFamilyMovements(treeId, selectedFamilyId, baseFilters)
        : mode === "compare"
        ? getGroupMovements(treeId, compareIds, baseFilters)
        : getMovements(treeId, baseFilters)

    fetcher
      .then(data => {
        // if API returns flat segments array:
        let segments = []
        if (Array.isArray(data) && data.length && data[0].event_type) {
          segments = data
        } else if (Array.isArray(data)) {
         // old shape: [{ person..., movements: [...] }, ...]
          segments = data.flatMap(person =>
            (person.movements || []).map(m => ({
              ...m,
              person_id:   person.person_id,
              person_name: person.name,
            }))
          )
        }
        setMovements(segments)
      })
      .catch(err => {
        console.error("❌ Movement fetch failed", err)
        devLog("❌ Movement fetch error →", err.message)
        setError("Failed to load movements.")
      })
      .finally(() => {
        setLoading(false)
        devLog("✅ Done fetching movements")
      })
  }, [treeId, filters])

  return (
    <div className="relative w-full h-full">
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 w-[90vw] max-w-4xl">
        <FilterHeader>
          <ModeSelector />
          {(activeSection === null || activeSection === "search") && <TypeSearch />}
          {activeSection === "person" && <PersonSelector />}
          {activeSection === "family" && <FamilySelector />}
          {activeSection === "compare" && <GroupSelector />}
          {activeSection === null && (
            <button
              onClick={() => toggleSection("filters")}
              className="text-sm text-accent hover:underline"
            >
              Filters
            </button>
          )}
        </FilterHeader>
      </div>

      {activeSection === "filters" && <AdvancedFilterDrawer />}
      <MapComponent movements={movements} loading={loading} error={error} />
      <LegendPanel />
    </div>
  )
}
