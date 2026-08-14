import { AlertCircle, ArrowRight, MapPin, Package } from 'lucide-react'

import { formatCLP } from '@/lib/format'

interface StepShippingProps {
  destinationName: string
  destinationRegion?: string
  tariff: number | null
  isLoading: boolean
  errorMessage: string | null
  onRetry: () => void
  onSubmit: () => void
  onBack: () => void
}

// Shipping step of the four-step checkout: presents the backend-computed
// tariff for the selected destination (guest quote or authenticated cart)
// and blocks continuation until a tariff is available.
export function StepShipping({ destinationName, destinationRegion, tariff, isLoading, errorMessage, onRetry, onSubmit, onBack }: StepShippingProps) {
  const canContinue = !isLoading && errorMessage === null && tariff !== null

  return (
    <fieldset>
      <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">Envío</legend>

      <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
        <MapPin size={13} className="mt-0.5 shrink-0 text-neon-lime" aria-hidden="true" />
        <p className="text-xs leading-relaxed text-muted-foreground">
          Envío a <strong className="text-foreground">{destinationName || '—'}</strong>
          {destinationRegion ? `, ${destinationRegion}` : ''}
        </p>
      </div>

      <div className="mb-5 rounded-2xl bg-secondary p-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">Tarifa de envío</span>
          {errorMessage === null && !isLoading && tariff !== null && (
            <span className="rounded-full border border-neon-lime/20 bg-neon-lime/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-neon-lime">Calculada por Código Secreto</span>
          )}
        </div>

        {errorMessage !== null ? (
          <div className="space-y-3" role="alert">
            <p className="flex items-center gap-1.5 text-xs text-destructive"><AlertCircle size={11} aria-hidden="true" /> {errorMessage}</p>
            <button type="button" onClick={onRetry} className="min-h-12 w-full rounded-xl border border-neon-cyan/60 px-4 text-xs font-bold uppercase text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button>
          </div>
        ) : isLoading || tariff === null ? (
          <p className="text-sm text-muted-foreground" role="status" aria-live="polite">Calculando el costo de envío…</p>
        ) : (
          <p className="text-lg font-extrabold text-foreground">{tariff === 0 ? 'Gratis' : formatCLP(tariff)}</p>
        )}
      </div>

      <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
        <Package size={13} className="mt-0.5 shrink-0 text-neon-lime" aria-hidden="true" />
        <p className="text-xs leading-relaxed text-muted-foreground">
          Todos los envíos van en caja neutra sin logos ni marcas. Remitente: <strong className="text-foreground">«CS Logistics»</strong>.
        </p>
      </div>

      <div className="flex gap-3 pt-4">
        <button type="button" onClick={onBack} className="rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Atrás</button>
        <button type="button" onClick={onSubmit} disabled={!canContinue} className="flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card disabled:cursor-not-allowed disabled:opacity-40" style={{ background: 'var(--gradient-brand)' }}>Siguiente <ArrowRight size={15} aria-hidden="true" /></button>
      </div>
    </fieldset>
  )
}
