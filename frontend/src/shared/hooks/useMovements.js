// frontend/src/shared/hooks/useMovements.js
import { useState, useEffect, useCallback } from "react"
import {
  getMovements,
  getFamilyMovements,
  getGroupMovements,
} from "@lib/api/api"
import { log as devLog } from "@/lib/api/devLogger.js"

const DEBUG = process.env.NODE_ENV === "development"

export default function useMovements(treeId, filters, mode) {
  const [movements, setMovements] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchMovements = useCallback(() => {
    if (!treeId) return
    setLoading(true)
    setError(null)
    DEBUG && devLog("useMovements", "🗺️ fetching", { treeId, filters, mode })

    const { selectedFamilyId, compareIds, ...baseFilters } = filters
    const fetcher =
      mode === "family"
        ? getFamilyMovements(treeId, selectedFamilyId, baseFilters)
        : mode === "compare"
        ? getGroupMovements(treeId, compareIds, baseFilters)
        : getMovements(treeId, baseFilters)

    fetcher
      .then((data) => {
        let segments = []
        if (Array.isArray(data) && data.length && data[0].event_type) {
          segments = data
        } else if (Array.isArray(data)) {
          segments = data.flatMap((person) =>
            (person.movements || []).map((m) => ({
              ...m,
              person_id: person.person_id,
              person_name: person.name,
            }))
          )
        }
        setMovements(segments)
      })
      .catch((err) => {
        console.error("❌ movement fetch failed", err)
        DEBUG && devLog("useMovements", "❌ error", err)
        setError("Failed to load movements.")
      })
      .finally(() => {
        setLoading(false)
        DEBUG && devLog("useMovements", "✅ done")
      })
  }, [treeId, filters, mode])

  useEffect(() => {
    fetchMovements()
  }, [fetchMovements])

  return { movements, loading, error }
}
