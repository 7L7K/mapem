import React from 'react'
import { useMapControl } from '@shared/context/MapControlContext'
import { useSearch } from '@shared/context/SearchContext'
import ModeSelector from '@shared/components/Header/ModeSelector'
import FilterHeader from '@shared/components/Header/FilterHeader'
import AdvancedFilterDrawer from './AdvancedFilterDrawer'
import TypeSearch from './TypeSearch'
import PersonSelector from './PersonSelector'
import FamilySelector from './FamilySelector'
import GroupSelector from './GroupSelector'
import { log as devLog } from '@/lib/api/devLogger.js'

export default function MapFilters() {
  const { activeSection, toggleSection } = useMapControl()
  const { filters, clearAll, setIsDrawerOpen } = useSearch()

  React.useEffect(() => {
    devLog('MapFilters', '🔄 active section', { activeSection })
  }, [activeSection])

  const openFilters = () => {
    devLog('MapFilters', '🧩 open AdvancedFilterDrawer')
    toggleSection('filters')
    setIsDrawerOpen(true)
  }

  return (
    <>
      <div className="sticky top-4 z-50 w-full px-4 md:px-6 flex justify-center">
        <FilterHeader>
          <ModeSelector />
          {(activeSection === null || activeSection === 'search') && <TypeSearch />}
          {activeSection === 'person' && <PersonSelector />}
          {activeSection === 'family' && <FamilySelector />}
          {activeSection === 'compare' && <GroupSelector />}
          {activeSection === null && (
            <button
              aria-label="Open Filters"
              onClick={openFilters}
              className="text-sm text-accent hover:underline"
            >
              Filters
            </button>
          )}

          {/* Active filters counter + clear */}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-white/60">
              {(() => {
                let count = 0
                if (filters.person) count++
                if (filters.vague) count++
                count += Object.values(filters.eventTypes || {}).filter(Boolean).length
                count += Object.values(filters.relations || {}).filter(Boolean).length
                count += Object.values(filters.sources || {}).filter(Boolean).length
                // yearRange different from default
                if (Array.isArray(filters.yearRange) && (filters.yearRange[0] !== 1800 || filters.yearRange[1] !== 2000)) count++
                return `${count} filter${count === 1 ? '' : 's'} applied`
              })()}
            </span>
            <button
              onClick={clearAll}
              className="text-xs text-white/70 hover:text-white underline-offset-2 hover:underline"
              title="Clear all filters"
            >
              Clear
            </button>
          </div>
        </FilterHeader>
      </div>

      {activeSection === 'filters' && <AdvancedFilterDrawer />}
    </>
  )
}
