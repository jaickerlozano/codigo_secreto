import { Lock, MessageCircle, Package, Truck } from 'lucide-react'

const benefits = [
  {
    icon: Package,
    label: 'Empaque 100% discreto',
    sub: 'Sin logos ni identificación',
  },
  {
    icon: Lock,
    label: 'Pago seguro',
    sub: 'Webpay, Flow, MercadoPago',
  },
  {
    icon: Truck,
    label: 'Envío rápido',
    sub: 'Santiago RM antes 16:00',
  },
  {
    icon: MessageCircle,
    label: 'Atención personalizada',
    sub: 'Soporte discreto',
  },
]

export function BenefitsSection() {
  return (
    <section
      className="border-y border-border bg-[#0f0f0f] py-5"
      aria-label="Beneficios"
    >
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-12">
          {benefits.map(({ icon: Icon, label, sub }) => (
            <div key={label} className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-neon-magenta/20 bg-neon-magenta/10"
                aria-hidden="true"
              >
                <Icon size={16} className="text-neon-magenta" />
              </div>
              <div>
                <p className="text-[12px] font-bold text-foreground">
                  {label}
                </p>
                <p className="text-[10px] text-muted-foreground">{sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
