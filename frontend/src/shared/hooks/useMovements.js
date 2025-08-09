// frontend/src/shared/hooks/useMovements.js
import { useState, useEffect, useCallback, useRef } from "react"
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

  const abortRef = useRef(null)

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
          : getMovements(treeId, { ...baseFilters, mode: 'segments' })

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    fetcher
      .then((data) => {
        if (controller.signal.aborted) return
        // Backend now returns segments for default mode
        const list = Array.isArray(data) ? data : []
        setMovements(list)
      })
      .catch((err) => {
        if (controller.signal.aborted) return
        console.error("❌ movement fetch failed", err)
        DEBUG && devLog("useMovements", "❌ error", err)
        setError("Failed to load movements.")
      })
      .finally(() => {
        if (controller.signal.aborted) return
        setLoading(false)
        DEBUG && devLog("useMovements", "✅ done")
      })
  }, [treeId, filters, mode])

  useEffect(() => {
    fetchMovements()
    return () => {
      if (abortRef.current) abortRef.current.abort()
    }
  }, [fetchMovements])

  return { movements, loading, error }
}
