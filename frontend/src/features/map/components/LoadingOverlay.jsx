import React from 'react'
import { Card } from '@shared/components/ui/Card'

export default function LoadingOverlay({ loading, error, empty }) {
  if (!loading && !error && !empty) return null

  let message = 'Loading...'
  if (error) message = error
  else if (empty) message = 'No data found.'

  return (
    <div
      className="absolute inset-0 z-40 flex items-center justify-center bg-black/60 text-white"
      role="status"
      aria-live="polite"
    >
      <Card className="bg-surface/90 backdrop-blur-md border-white/10">
        <p className="px-4 py-2 text-sm">{message}</p>
      </Card>
    </div>
  )
}
