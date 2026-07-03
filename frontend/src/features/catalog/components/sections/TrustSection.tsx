import { Lock, Package, Shield } from 'lucide-react'

const trustItems = [
  {
    icon: Package,
    title: 'Empaque 100% discreto',
    description:
      'Todos los envíos llegan en caja neutra sin logos ni marcas. Remitente: «CS Logistics».',
    accent: '#a3e635',
  },
  {
    icon: Lock,
    title: 'Pago 100% seguro',
    description:
      'Webpay, Flow y MercadoPago. Nunca almacenamos datos de tu tarjeta. SSL certificado.',
    accent: '#ff2bd6',
  },
  {
    icon: Shield,
    title: 'Privacidad total',
    description:
      'Solo recopilamos los datos mínimos para tu pedido. Sin retargeting, sin historial público.',
    accent: '#00f0ff',
  },
]

export function TrustSection() {
  return (
    <section
      className="border-t border-border bg-[#0f0f0f] py-20 px-4"
      aria-label="Privacidad"
    >
      <div className="mx-auto max-w-4xl">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-extrabold uppercase tracking-wide text-foreground">
            Tu privacidad es nuestra prioridad
          </h2>
          <p className="mx-auto max-w-md text-sm leading-relaxed text-muted-foreground">
            Cada aspecto del servicio fue diseñado para que compres con
            total tranquilidad.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-3">
          {trustItems.map(({ icon: Icon, title, description, accent }) => (
            <div
              key={title}
              className="group rounded-2xl border border-border bg-card p-6 text-center transition-colors hover:border-white/12"
            >
              <div
                className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl transition-all group-hover:scale-110"
                style={{
                  backgroundColor: `${accent}12`,
                  border: `1px solid ${accent}25`,
                }}
                aria-hidden="true"
              >
                <Icon size={24} style={{ color: accent }} />
              </div>
              <h3 className="mb-2 text-[14px] font-extrabold uppercase tracking-wide text-foreground">
                {title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
