import { AlertTriangle } from 'lucide-react'

import { Card } from './ui'

export function LoadingState({ label = 'Loading data…' }: { label?: string }) {
  return (
    <Card className="p-10">
      <div className="space-y-4">
        <div className="h-3 w-28 animate-pulse rounded-full bg-border" />
        <div className="h-12 w-64 animate-pulse rounded-3xl bg-border/90" />
        <div className="h-6 w-full animate-pulse rounded-full bg-border/70" />
        <div className="text-sm text-charcoal/50">{label}</div>
      </div>
    </Card>
  )
}

export function ErrorState({ error }: { error: Error }) {
  return (
    <Card className="border-red-200 bg-red-50 p-8">
      <div className="flex items-start gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-2xl bg-red-100 text-red-600">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <div className="font-display text-2xl text-charcoal">Something interrupted the page.</div>
          <div className="mt-2 text-sm leading-6 text-charcoal/70">{error.message}</div>
        </div>
      </div>
    </Card>
  )
}
