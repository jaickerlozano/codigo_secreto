import { motion } from 'motion/react'
import {
  Building2,
  Check,
  CheckCircle2,
  Copy,
  Mail,
  Package,
  Truck,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

const ORDER_STORAGE_KEY = 'cs-last-order'

const TIMELINE = [
  { label: 'Pedido recibido', done: true },
  { label: 'En preparación', active: true },
  { label: 'Despachado', done: false, active: false },
  { label: 'Entregado', done: false, active: false },
]

export function ConfirmationPage() {
  const navigate = useNavigate()
  const [orderNumber, setOrderNumber] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const stored = sessionStorage.getItem(ORDER_STORAGE_KEY)
    if (!stored) {
      navigate('/', { replace: true })
      return
    }
    setOrderNumber(stored)
  }, [navigate])

  if (!orderNumber) {
    return null
  }

  const handleCopy = () => {
    navigator.clipboard?.writeText(orderNumber).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleGoHome = () => {
    navigate('/', { replace: true })
  }

  return (
    <main
      id="main-content"
      className="flex min-h-screen items-center justify-center px-4 py-16"
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className="w-full max-w-md text-center"
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="relative mx-auto mb-8 h-24 w-24"
        >
          <div
            className="absolute inset-0 animate-ping rounded-full bg-neon-lime/15"
            aria-hidden="true"
          />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-neon-lime/25 bg-neon-lime/10">
            <CheckCircle2
              size={40}
              className="text-neon-lime"
              aria-hidden="true"
            />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-3 text-3xl font-extrabold uppercase tracking-wide text-foreground"
        >
          ¡Pedido confirmado!
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mx-auto mb-10 max-w-xs text-sm leading-relaxed text-muted-foreground"
        >
          Recibirás una confirmación discreta en tu email en los próximos
          minutos.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="mb-5 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <div className="mb-5 flex items-center justify-between border-b border-white/[0.06] pb-5">
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                Número de pedido
              </p>
              <p className="font-mono text-xl font-extrabold text-foreground">
                {orderNumber}
              </p>
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-xl bg-secondary p-2.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={`Copiar ${orderNumber}`}
              aria-live="polite"
            >
              {copied ? (
                <Check size={15} className="text-neon-lime" />
              ) : (
                <Copy size={15} className="text-muted-foreground" />
              )}
            </button>
          </div>

          <div className="space-y-4">
            {[
              { icon: Mail, label: 'Confirmación', value: 'Enviada a tu email' },
              {
                icon: Package,
                label: 'Embalaje',
                value: 'Discreto — sin logos ni marcas',
              },
              { icon: Building2, label: 'Remitente', value: 'CS Logistics (neutro)' },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-center gap-3.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary">
                  <Icon size={14} className="text-muted-foreground" aria-hidden="true" />
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">{label}</p>
                  <p className="text-sm text-foreground">{value}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="mb-8 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <p className="mb-5 text-[10px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground">
            Estado del pedido
          </p>
          {TIMELINE.map(({ label, done, active }) => (
            <div key={label} className="mb-3 flex items-center gap-4 last:mb-0">
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                  done
                    ? 'bg-neon-lime'
                    : active
                      ? 'text-foreground ring-4 ring-neon-magenta/20'
                      : 'bg-secondary'
                }`}
                style={active ? { background: 'var(--gradient-brand)' } : undefined}
                aria-hidden="true"
              >
                {done && <Check size={13} className="text-background" />}
              </div>
              <span
                className={`text-sm ${
                  done || active
                    ? 'font-semibold text-foreground'
                    : 'text-muted-foreground'
                }`}
              >
                {label}
              </span>
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
          className="mb-8 flex items-start gap-3 rounded-2xl border border-neon-lime/20 bg-neon-lime/10 p-4 text-left"
        >
          <Truck
            size={16}
            className="mt-0.5 shrink-0 text-neon-lime"
            aria-hidden="true"
          />
          <p className="text-xs leading-relaxed text-neon-lime">
            <strong>CS Logistics:</strong> Tu pedido será preparado y enviado en
            empaque 100% neutro. El remitente no identifica el contenido para
            proteger tu privacidad.
          </p>
        </motion.div>

        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          type="button"
          onClick={handleGoHome}
          className="w-full rounded-xl py-4 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </motion.button>
      </motion.div>
    </main>
  )
}
