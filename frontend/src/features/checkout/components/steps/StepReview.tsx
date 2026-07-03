import { Check, Lock, Package } from 'lucide-react'

import { formatCLP } from '@/lib/format'

import { PAYMENT_OPTIONS, SHIPPING_OPTIONS } from '../../data'
import type { CheckoutData, CheckoutStep } from '../../types'

interface StepReviewProps {
  data: CheckoutData
  subtotal: number
  shippingCost: number
  total: number
  onEditStep: (step: CheckoutStep) => void
  onTermsChange: (accepted: boolean) => void
  onBack: () => void
  onConfirm: () => void
}

export function StepReview({
  data,
  subtotal,
  shippingCost,
  total,
  onEditStep,
  onTermsChange,
  onBack,
  onConfirm,
}: StepReviewProps) {
  const shippingLabel =
    SHIPPING_OPTIONS.find((s) => s.id === data.shipping.carrier)?.name ?? '—'
  const paymentLabel =
    PAYMENT_OPTIONS.find((p) => p.id === data.payment.method)?.name ?? '—'

  const summaryItems = [
    { label: 'Contacto', value: data.contact.email, step: 1 as CheckoutStep },
    {
      label: 'Dirección',
      value: data.address.address
        ? `${data.address.address}${data.address.apartment ? `, ${data.address.apartment}` : ''}, ${data.address.comuna}, ${data.address.region}`
        : '—',
      step: 2 as CheckoutStep,
    },
    { label: 'Envío', value: shippingLabel, step: 3 as CheckoutStep },
    { label: 'Pago', value: paymentLabel, step: 4 as CheckoutStep },
  ]

  return (
    <div>
      <h2 className="mb-6 text-xl font-extrabold uppercase tracking-wide text-foreground">
        Revisar y confirmar
      </h2>

      <div className="mb-6 space-y-3">
        {summaryItems.map(({ label, value, step }) => (
          <div
            key={label}
            className="flex items-start justify-between rounded-2xl bg-secondary p-4"
          >
            <div className="mr-4 min-w-0 flex-1">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                {label}
              </p>
              <p className="text-sm text-foreground">{value}</p>
            </div>
            <button
              type="button"
              onClick={() => onEditStep(step)}
              className="shrink-0 rounded text-xs text-neon-magenta hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Editar
            </button>
          </div>
        ))}
      </div>

      <div className="mb-6 rounded-2xl bg-secondary p-4">
        <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
          Productos
        </p>
        <p className="text-sm text-muted-foreground">
          Revisa los productos en el resumen del pedido a la derecha.
        </p>
      </div>

      <div className="mb-6 rounded-2xl bg-secondary p-4">
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Subtotal</span>
          <span className="text-foreground">{formatCLP(subtotal)}</span>
        </div>
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Envío</span>
          <span
            className={
              shippingCost === 0 ? 'text-neon-lime' : 'text-foreground'
            }
          >
            {shippingCost === 0 ? 'Gratis' : formatCLP(shippingCost)}
          </span>
        </div>
        <div className="flex justify-between border-t border-white/[0.06] pt-3 text-[17px] font-extrabold">
          <span className="text-foreground">Total</span>
          <span className="text-foreground">{formatCLP(total)}</span>
        </div>
      </div>

      <label className="group mb-5 flex cursor-pointer items-start gap-3">
        <div
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition-all ${
            data.termsAccepted
              ? 'border-neon-magenta bg-neon-magenta'
              : 'border-[#333] group-hover:border-neon-magenta/50'
          }`}
          aria-hidden="true"
        >
          {data.termsAccepted && <Check size={12} className="text-background" />}
        </div>
        <input
          type="checkbox"
          checked={data.termsAccepted}
          onChange={(e) => onTermsChange(e.target.checked)}
          className="sr-only"
          aria-required="true"
        />
        <p className="text-xs leading-relaxed text-muted-foreground">
          Acepto los{' '}
          <button
            type="button"
            className="text-neon-magenta hover:underline focus-visible:outline-none"
          >
            Términos de Uso
          </button>{' '}
          y la{' '}
          <button
            type="button"
            className="text-neon-magenta hover:underline focus-visible:outline-none"
          >
            Política de Privacidad
          </button>
          . Confirmo que soy mayor de 18 años.
        </p>
      </label>

      <div className="mb-5 flex items-start gap-3 rounded-2xl bg-secondary p-4">
        <Package
          size={13}
          className="mt-0.5 shrink-0 text-neon-lime"
          aria-hidden="true"
        />
        <p className="text-xs text-muted-foreground">
          Pedido enviado en empaque 100% discreto. Remitente:{' '}
          <strong className="text-foreground">«CS Logistics»</strong>.
        </p>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="rounded-xl border border-white/10 px-6 py-3 text-sm font-bold uppercase tracking-wide text-muted-foreground transition-all hover:border-white/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Atrás
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={!data.termsAccepted}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card disabled:cursor-not-allowed disabled:opacity-40"
          style={{ background: 'var(--gradient-brand)' }}
        >
          <Lock size={15} aria-hidden="true" /> Confirmar pedido
        </button>
      </div>

      <p className="mt-4 flex items-center justify-center gap-1.5 text-center text-[10px] text-muted-foreground">
        <Lock size={9} className="text-neon-lime" aria-hidden="true" /> Tus
        datos están protegidos con encriptación SSL
      </p>
    </div>
  )
}
