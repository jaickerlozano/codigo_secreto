import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle, ArrowRight, CalendarDays, MapPin, Package } from 'lucide-react'

import { formatCLP } from '@/lib/format'
import { getDispatchOptions } from '@/features/shipping/api/shipping.api'

import {
  formatDispatchDate,
  isDispatchSelectionValid,
} from '../../lib/shipping-selection'
import type { ShippingData } from '../../types'

interface StepShippingProps {
  comunaId: number | null
  destinationName: string
  destinationRegion?: string
  shippingCost: number | null
  quoteIsLoading: boolean
  quoteIsError: boolean
  quoteError: Error | null
  onRetryQuote: () => void
  selection: ShippingData
  onSubmit: (selection: ShippingData) => void
  onBack: () => void
}

function tomorrowIso(): string {
  const next = new Date()
  next.setDate(next.getDate() + 1)
  const month = String(next.getMonth() + 1).padStart(2, '0')
  const day = String(next.getDate()).padStart(2, '0')
  return `${next.getFullYear()}-${month}-${day}`
}

const radioCardClass = 'flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-secondary px-4 transition-all has-[:checked]:border-neon-cyan/70 has-[:checked]:bg-neon-cyan/5'

// Shipping step of the four-step checkout: presents the backend dispatch
// options for the destination comuna and blocks continuation until an explicit
// selection (Santiago date, special date, or regional option) is confirmed.
export function StepShipping({ comunaId, destinationName, destinationRegion, shippingCost, quoteIsLoading, quoteIsError, quoteError, onRetryQuote, selection, onSubmit, onBack }: StepShippingProps) {
  const [picked, setPicked] = useState<ShippingData>(selection)
  const [customMode, setCustomMode] = useState(false)
  const [customDate, setCustomDate] = useState('')
  const [invalidated, setInvalidated] = useState(false)

  const dispatch = useQuery({
    queryKey: ['dispatch-options', comunaId],
    queryFn: () => getDispatchOptions(comunaId as number),
    enabled: comunaId !== null && comunaId > 0,
    retry: false,
  })
  const options = dispatch.data ?? null
  const regionalOption = options !== null && options.mode === 'regional' ? options.shippingOption : null

  useEffect(() => {
    if (options && Object.keys(picked).length > 0 && !isDispatchSelectionValid(picked, options)) {
      setPicked({})
      setCustomMode(false)
      setCustomDate('')
      setInvalidated(true)
    }
    // Re-validate only when fresh options arrive (mount, comuna change, retry).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options])

  const quoteReady = !quoteIsLoading && !quoteIsError && shippingCost !== null
  const optionsReady = !dispatch.isLoading && !dispatch.isError && options !== null
  const selectionReady = options !== null && isDispatchSelectionValid(picked, options)
  const canContinue = quoteReady && optionsReady && selectionReady

  const chooseStandard = (date: string) => {
    setInvalidated(false)
    setCustomMode(false)
    setCustomDate('')
    setPicked({ deliveryKind: 'standard', requestedDispatchDate: date })
  }

  const chooseCustom = () => {
    setInvalidated(false)
    setCustomMode(true)
    setCustomDate('')
    setPicked({})
  }

  const changeCustomDate = (value: string) => {
    setCustomDate(value)
    setInvalidated(false)
    setPicked(value ? { deliveryKind: 'special', requestedDispatchDate: value } : {})
  }

  const chooseOption = (optionId: number) => {
    setInvalidated(false)
    setCustomMode(false)
    setCustomDate('')
    setPicked({ deliveryKind: 'standard', shippingOptionId: optionId })
  }

  const handleSubmit = () => {
    if (canContinue) onSubmit(picked)
  }

  const invalidatedNotice = invalidated && <p className="mb-2 text-xs text-neon-cyan" role="status" aria-live="polite">Tu selección anterior ya no está disponible. Elige nuevamente.</p>

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
          {quoteReady && (
            <span className="rounded-full border border-neon-lime/20 bg-neon-lime/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-neon-lime">Calculada por Código Secreto</span>
          )}
        </div>

        {quoteIsError ? (
          <div className="space-y-3" role="alert">
            <p className="flex items-center gap-1.5 text-xs text-destructive"><AlertCircle size={11} aria-hidden="true" /> {quoteError?.message ?? 'No pudimos calcular el costo de envío.'}</p>
            <button type="button" onClick={onRetryQuote} className="min-h-12 w-full rounded-xl border border-neon-cyan/60 px-4 text-xs font-bold uppercase text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button>
          </div>
        ) : quoteIsLoading || shippingCost === null ? (
          <p className="text-sm text-muted-foreground" role="status" aria-live="polite">Calculando el costo de envío…</p>
        ) : (
          <p className="text-lg font-extrabold text-foreground">{shippingCost === 0 ? 'Gratis' : formatCLP(shippingCost)}</p>
        )}
      </div>

      {comunaId === null || comunaId === 0 ? (
        <div className="mb-5 rounded-2xl bg-secondary p-4" role="alert">
          <p className="text-xs text-destructive">Selecciona una comuna en el paso anterior para ver las opciones de envío.</p>
        </div>
      ) : dispatch.isError ? (
        <div className="mb-5 space-y-3 rounded-2xl bg-secondary p-4" role="alert">
          <p className="flex items-center gap-1.5 text-xs text-destructive"><AlertCircle size={11} aria-hidden="true" /> {dispatch.error?.message ?? 'No pudimos cargar las opciones de envío.'}</p>
          <button type="button" onClick={() => void dispatch.refetch()} className="min-h-12 w-full rounded-xl border border-neon-cyan/60 px-4 text-xs font-bold uppercase text-neon-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Reintentar</button>
        </div>
      ) : dispatch.isLoading || options === null ? (
        <div className="mb-5 rounded-2xl bg-secondary p-4" role="status" aria-live="polite">
          <p className="text-sm text-muted-foreground">Cargando opciones de envío…</p>
        </div>
      ) : options.mode === 'santiago' && options.dates && options.dates.length > 0 ? (
        <div className="mb-5">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">Fecha de despacho</p>
          {invalidatedNotice}
          <div role="radiogroup" aria-label="Fecha de despacho" className="space-y-2">
            {options.dates.map((date) => (
              <label key={date} className={radioCardClass}>
                <input type="radio" name="dispatch-date" value={date} checked={picked.deliveryKind === 'standard' && picked.requestedDispatchDate === date} onChange={() => chooseStandard(date)} className="h-4 w-4 accent-neon-cyan" />
                <CalendarDays size={14} className="shrink-0 text-neon-lime" aria-hidden="true" />
                <span className="text-sm font-semibold text-foreground">{formatDispatchDate(date)}</span>
              </label>
            ))}
            <label className={radioCardClass}>
              <input type="radio" name="dispatch-date" checked={customMode} onChange={chooseCustom} className="h-4 w-4 accent-neon-cyan" />
              <span className="text-sm font-semibold text-foreground">Solicitar otra fecha</span>
            </label>
          </div>
          {customMode && (
            <div className="mt-3 rounded-xl border border-neon-cyan/30 bg-secondary p-4">
              <label htmlFor="special-dispatch-date" className="mb-1 block text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">Fecha deseada</label>
              <input id="special-dispatch-date" type="date" min={tomorrowIso()} value={customDate} onChange={(e) => changeCustomDate(e.target.value)} className="min-h-12 w-full rounded-xl border border-white/10 bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
              <p className="mt-1 text-[10px] text-muted-foreground">La entrega especial requiere confirmación previa por WhatsApp.</p>
            </div>
          )}
        </div>
      ) : regionalOption ? (
        <div className="mb-5">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">Envío regional</p>
          {invalidatedNotice}
          <label className={radioCardClass}>
            <input type="radio" name="dispatch-regional" checked={picked.shippingOptionId === regionalOption.shippingOptionId} onChange={() => chooseOption(regionalOption.shippingOptionId)} className="h-4 w-4 accent-neon-cyan" />
            <span className="flex-1">
              <span className="flex items-center justify-between gap-2">
                <span className="text-sm font-bold text-foreground">{regionalOption.carrier}</span>
                <span className="text-sm font-extrabold text-foreground">{regionalOption.tariff === 0 ? 'Gratis' : formatCLP(regionalOption.tariff)}</span>
              </span>
              <span className="text-xs text-muted-foreground">Entrega en {regionalOption.minLeadDays}–{regionalOption.maxLeadDays} días hábiles · Embalaje discreto</span>
            </span>
          </label>
        </div>
      ) : (
        <div className="mb-5 rounded-2xl bg-secondary p-4" role="alert">
          <p className="flex items-center gap-1.5 text-xs text-destructive"><AlertCircle size={11} aria-hidden="true" /> El envío no está disponible para esta comuna.</p>
        </div>
      )}

      <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
        <Package size={13} className="mt-0.5 shrink-0 text-neon-lime" aria-hidden="true" />
        <p className="text-xs leading-relaxed text-muted-foreground">
          Todos los envíos van en caja neutra sin logos ni marcas. Remitente: <strong className="text-foreground">«CS Logistics»</strong>.
        </p>
      </div>

      <div className="flex gap-3 pt-4">
        <button type="button" onClick={onBack} className="rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Atrás</button>
        <button type="button" onClick={handleSubmit} disabled={!canContinue} className="flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card disabled:cursor-not-allowed disabled:opacity-40" style={{ background: 'var(--gradient-brand)' }}>Siguiente <ArrowRight size={15} aria-hidden="true" /></button>
      </div>
    </fieldset>
  )
}