import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, ArrowRight, Package } from 'lucide-react'
import { useForm } from 'react-hook-form'

import { formatCLP } from '@/lib/format'

import { SHIPPING_OPTIONS } from '../../data'
import { shippingSchema, type ShippingSchema } from '../../schemas/checkout.schema'

interface StepShippingProps {
  defaultValues: ShippingSchema
  onSubmit: (data: ShippingSchema) => void
  onBack: () => void
}

export function StepShipping({
  defaultValues,
  onSubmit,
  onBack,
}: StepShippingProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ShippingSchema>({
    resolver: zodResolver(shippingSchema),
    defaultValues,
  })

  const selectedCarrier = watch('carrier')

  return (
    <fieldset>
      <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
        Método de envío
      </legend>

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div
          className="mb-5 space-y-3"
          role="radiogroup"
          aria-label="Opciones de envío"
        >
          {SHIPPING_OPTIONS.map((opt) => {
            const isSelected = selectedCarrier === opt.id

            return (
              <label
                key={opt.id}
                className={`flex cursor-pointer items-center gap-4 rounded-2xl border p-4 transition-all ${
                  isSelected
                    ? 'border-neon-cyan/60 bg-neon-cyan/6'
                    : 'border-white/[0.06] bg-secondary hover:border-white/15'
                }`}
              >
                <input
                  type="radio"
                  value={opt.id}
                  className="sr-only"
                  aria-label={`${opt.name} — ${opt.eta} — ${opt.price === 0 ? 'Gratis' : formatCLP(opt.price)}`}
                  {...register('carrier')}
                />
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                    isSelected ? 'border-neon-cyan' : 'border-[#333]'
                  }`}
                  aria-hidden="true"
                >
                  {isSelected && (
                    <div className="h-2.5 w-2.5 rounded-full bg-neon-cyan" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="mb-0.5 flex items-center gap-2">
                    <span className="text-[13px] font-bold uppercase tracking-wide text-foreground">
                      {opt.name}
                    </span>
                    <span className="rounded-full border border-neon-lime/20 bg-neon-lime/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-neon-lime">
                      Discreto
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {opt.description} · {opt.eta}
                  </p>
                </div>
                <span
                  className={`text-[13px] font-bold ${
                    opt.price === 0 ? 'text-neon-lime' : 'text-foreground'
                  }`}
                >
                  {opt.price === 0 ? 'Gratis' : formatCLP(opt.price)}
                </span>
              </label>
            )
          })}
        </div>

        {errors.carrier && (
          <p
            className="mb-4 flex items-center gap-1.5 text-xs text-destructive"
            role="alert"
          >
            <AlertCircle size={11} aria-hidden="true" />{' '}
            {errors.carrier.message}
          </p>
        )}

        <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
          <Package
            size={13}
            className="mt-0.5 shrink-0 text-neon-lime"
            aria-hidden="true"
          />
          <p className="text-xs text-muted-foreground leading-relaxed">
            Todos los envíos van en caja neutra sin logos ni marcas. Remitente:{' '}
            <strong className="text-foreground">«CS Logistics»</strong>.
          </p>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onBack}
            className="rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Atrás
          </button>
          <button
            type="submit"
            className="flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Siguiente <ArrowRight size={15} aria-hidden="true" />
          </button>
        </div>
      </form>
    </fieldset>
  )
}
