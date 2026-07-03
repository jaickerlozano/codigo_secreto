import { zodResolver } from '@hookform/resolvers/zod'
import {
  AlertCircle,
  ArrowRight,
  Building2,
  CreditCard,
  Lock,
  QrCode,
  Wallet,
} from 'lucide-react'
import { useForm } from 'react-hook-form'

import { PAYMENT_OPTIONS } from '../../data'
import { paymentSchema, type PaymentSchema } from '../../schemas/checkout.schema'

const ICON_MAP = {
  'credit-card': CreditCard,
  wallet: Wallet,
  'qr-code': QrCode,
  'building-2': Building2,
}

interface StepPaymentProps {
  defaultValues: PaymentSchema
  onSubmit: (data: PaymentSchema) => void
  onBack: () => void
}

export function StepPayment({
  defaultValues,
  onSubmit,
  onBack,
}: StepPaymentProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<PaymentSchema>({
    resolver: zodResolver(paymentSchema),
    defaultValues,
  })

  const selectedMethod = watch('method')

  return (
    <fieldset>
      <legend className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
        Método de pago
      </legend>

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div
          className="mb-5 space-y-3"
          role="radiogroup"
          aria-label="Métodos de pago"
        >
          {PAYMENT_OPTIONS.map((opt) => {
            const isSelected = selectedMethod === opt.id
            const Icon = ICON_MAP[opt.icon as keyof typeof ICON_MAP] ?? CreditCard

            return (
              <label
                key={opt.id}
                className={`flex cursor-pointer items-center gap-4 rounded-2xl border p-4 transition-all ${
                  isSelected
                    ? 'border-neon-magenta/50 bg-neon-magenta/6'
                    : 'border-white/[0.06] bg-secondary hover:border-white/15'
                }`}
              >
                <input
                  type="radio"
                  value={opt.id}
                  className="sr-only"
                  aria-label={opt.name}
                  {...register('method')}
                />
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                    isSelected ? 'border-neon-magenta' : 'border-[#333]'
                  }`}
                  aria-hidden="true"
                >
                  {isSelected && (
                    <div className="h-2.5 w-2.5 rounded-full bg-neon-magenta" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="mb-0.5 flex items-center gap-2">
                    <span className="text-[13px] font-bold text-foreground">
                      {opt.name}
                    </span>
                    {opt.id === 'webpay' && (
                      <span className="rounded-full border border-neon-magenta/20 bg-neon-magenta/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-neon-magenta">
                        Recomendado
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {opt.description}
                  </p>
                </div>
                <Icon
                  size={18}
                  className="shrink-0 text-muted-foreground"
                  aria-hidden="true"
                />
              </label>
            )
          })}
        </div>

        {errors.method && (
          <p
            className="mb-4 flex items-center gap-1.5 text-xs text-destructive"
            role="alert"
          >
            <AlertCircle size={11} aria-hidden="true" />{' '}
            {errors.method.message}
          </p>
        )}

        <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
          <Lock
            size={13}
            className="mt-0.5 shrink-0 text-neon-lime"
            aria-hidden="true"
          />
          <p className="text-xs text-muted-foreground">
            Pago 100% seguro y encriptado. Nunca almacenamos datos de tu
            tarjeta.
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
