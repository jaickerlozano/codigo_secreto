import { CreditCard, Truck } from 'lucide-react'

const paymentMethods = [
  'Webpay',
  'Flow',
  'MercadoPago',
  'Transferencia',
]

const carriers = [
  'Chilexpress',
  'Starken',
  'Bluexpress',
  'Express Santiago',
]

export function PaymentLogosSection() {
  return (
    <section
      className="border-y border-border bg-[#0f0f0f] py-10 px-4"
      aria-label="Pagos y envíos"
    >
      <div className="mx-auto max-w-4xl text-center">
        <p className="mb-5 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
          Métodos de pago aceptados
        </p>
        <div className="mb-6 flex flex-wrap items-center justify-center gap-5 sm:gap-10">
          {paymentMethods.map((method) => (
            <span
              key={method}
              className="inline-flex items-center gap-1.5 text-[12px] font-bold text-muted-foreground transition-colors hover:text-foreground"
            >
              <CreditCard size={12} aria-hidden="true" />
              {method}
            </span>
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-center gap-6 text-[11px] text-muted-foreground">
          {carriers.map((carrier) => (
            <span
              key={carrier}
              className="flex items-center gap-1.5"
            >
              <Truck size={11} aria-hidden="true" /> {carrier}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
