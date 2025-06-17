import React from 'react'
import { useMapControl } from '@shared/context/MapControlContext'
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

  React.useEffect(() => {
    devLog('MapFilters', '🔄 active section', { activeSection })
  }, [activeSection])

  const openFilters = () => {
    devLog('MapFilters', '🧩 open AdvancedFilterDrawer')
    toggleSection('filters')
  }

  return (
    <>
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 w-[90vw] max-w-4xl">
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
        </FilterHeader>
      </div>

      {activeSection === 'filters' && <AdvancedFilterDrawer />}
    </>
  )
}
