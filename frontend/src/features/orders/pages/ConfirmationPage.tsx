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
import { Link, useLocation, useNavigate, useParams } from 'react-router'

import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/features/auth/context/AuthContext'
import { useCartStore } from '@/features/cart'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { formatCLP } from '@/lib/format'
import type { components } from '@/api/schema.d.ts'

import { useOrder } from '../hooks/useOrder'

type OrderStatus = components['schemas']['OrderStatusEnum']
type PaymentMethod = components['schemas']['Order']['payment_method']

const STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING: 'Pendiente de pago',
  PAID: 'Pagado / Listo para despacho',
  SHIPPED: 'Enviado a destino',
  DELIVERED: 'Entregado',
  CANCELLED: 'Cancelado',
}

const PAYMENT_METHOD_LABELS: Record<NonNullable<PaymentMethod>, string> = {
  webpay: 'Webpay / Tarjeta bancaria',
  flow: 'Flow',
  mercadopago: 'Mercado Pago',
  transfer: 'Transferencia bancaria',
}

const FULFILLMENT_ROWS = [
  { icon: Mail, label: 'Confirmación', value: 'Enviada a tu email' },
  { icon: Package, label: 'Embalaje', value: 'Discreto — sin logos ni marcas' },
  { icon: Building2, label: 'Remitente', value: 'CS Logistics (neutro)' },
]

export function ConfirmationPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams()
  const stateOrderNumber = typeof location.state === 'object' && location.state !== null && 'orderNumber' in location.state && typeof location.state.orderNumber === 'string' ? location.state.orderNumber : null
  const orderNumber = params.orderNumber ?? stateOrderNumber
  const [copied, setCopied] = useState(false)
  const prefersReduced = useReducedMotion()
  const cartMode = useCartStore((state) => state.mode)
  const { isAuthenticated } = useAuth()
  const { data: order, isLoading, error } = useOrder(orderNumber ?? undefined)

  useEffect(() => {
    if (!orderNumber) navigate('/', { replace: true })
    else if (order?.status === 'PENDING') navigate(`/checkout/payment/${orderNumber}`, { replace: true })
    else if (order?.status === 'PAID' && cartMode === 'guest') useCartStore.getState().clearCart()
  }, [navigate, order, orderNumber, cartMode])

  const handleCopy = () => {
    if (!orderNumber) return
    navigator.clipboard?.writeText(orderNumber).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleGoHome = () => {
    navigate('/', { replace: true })
  }

  if (!orderNumber) {
    return null
  }

  if (isLoading) {
    return (
      <main
        id="main-content"
        className="flex min-h-screen items-center justify-center px-4 py-16"
      >
        <LoadingSpinner />
      </main>
    )
  }

  if (error || !order) {
    return (
      <main
        id="main-content"
        className="flex min-h-screen items-center justify-center px-4 py-16"
      >
        <div className="w-full max-w-md text-center">
          <p className="mb-6 text-sm text-muted-foreground">
            {error?.message || 'No pudimos cargar los detalles del pedido.'}
          </p>
          <button
            type="button"
            onClick={handleGoHome}
            className="w-full rounded-xl py-4 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Volver al inicio
          </button>
        </div>
      </main>
    )
  }

  const isGuest = Boolean(order.guest_email)
  const isCancelled = order.status === 'CANCELLED'

  return (
    <main
      id="main-content"
      className="flex min-h-screen items-center justify-center px-4 py-16"
    >
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={prefersReduced ? { duration: 0 } : { duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className="w-full max-w-md text-center"
      >
        <motion.div
          initial={prefersReduced ? false : { scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.1, duration: 0.4 }}
          className="relative mx-auto mb-8 h-24 w-24"
        >
          <div
            className={`absolute inset-0 rounded-full bg-neon-lime/15 ${prefersReduced ? '' : 'animate-ping'}`}
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
          initial={prefersReduced ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.2 }}
          className="mb-3 text-3xl font-extrabold uppercase tracking-wide text-foreground"
        >
          {isCancelled ? 'Pedido cancelado' : '¡Pedido confirmado!'}
        </motion.h1>

        <motion.p
          initial={prefersReduced ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.3 }}
          className="mx-auto mb-10 max-w-xs text-sm leading-relaxed text-muted-foreground"
        >
          {isCancelled
            ? 'Este pedido fue cancelado y no será despachado.'
            : 'Recibirás una confirmación discreta en tu email en los próximos minutos.'}
        </motion.p>

        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.35 }}
          className="mb-5 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <div className="mb-5 flex items-center justify-between border-b border-white/[0.06] pb-5">
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                Número de pedido
              </p>
              <p className="font-mono text-xl font-extrabold text-foreground">
                {order.order_number}
              </p>
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-xl bg-secondary p-2.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={`Copiar ${order.order_number}`}
              aria-live="polite"
            >
              {copied ? (
                <Check size={15} className="text-neon-lime" />
              ) : (
                <Copy size={15} className="text-muted-foreground" />
              )}
            </button>
          </div>

          <div className="mb-5 flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              Estado del pago
            </p>
            <span className="rounded-full bg-neon-cyan/10 px-2.5 py-1 text-xs font-bold text-neon-cyan">
              {STATUS_LABELS[order.status]}
            </span>
          </div>

          <div className="space-y-4">
            {[
              ...(isCancelled ? [] : FULFILLMENT_ROWS),
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
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.4 }}
          className="mb-5 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <p className="mb-4 text-[10px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground">
            Resumen de tu compra
          </p>

          <ul className="mb-4 space-y-3">
            {order.items.map((item) => (
              <li
                key={item.id}
                className="flex items-start justify-between gap-3 text-sm"
              >
                <div>
                  <p className="font-semibold text-foreground">{item.product_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.quantity}{' '}
                    {item.quantity === 1 ? 'unidad' : 'unidades'}
                  </p>
                </div>
                <span className="font-semibold text-foreground">
                  {formatCLP(item.subtotal)}
                </span>
              </li>
            ))}
          </ul>

          <div className="space-y-2 border-t border-white/[0.06] pt-4 text-sm">
            <div className="flex justify-between text-muted-foreground">
              <span>Subtotal</span>
              <span>{formatCLP(order.subtotal)}</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>Envío</span>
              <span>
                {order.shipping_cost === 0
                  ? 'Gratis'
                  : formatCLP(order.shipping_cost)}
              </span>
            </div>
            <div className="flex justify-between font-bold text-foreground">
              <span>Total</span>
              <span>{formatCLP(order.total)}</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.45 }}
          className="mb-5 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <p className="mb-4 text-[10px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground">
            Dirección de envío
          </p>
          <div className="space-y-1 text-sm">
            <p className="font-semibold text-foreground">
              {order.guest_name || 'Cliente'}
            </p>
            <p className="text-muted-foreground">{order.shipping_address}</p>
            {order.apartment_office && (
              <p className="text-muted-foreground">{order.apartment_office}</p>
            )}
            <p className="text-muted-foreground">
              {order.comuna_name}, {order.region_name}
            </p>
            <p className="text-muted-foreground">{order.phone}</p>
          </div>
        </motion.div>

        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.5 }}
          className="mb-8 rounded-2xl border border-white/[0.06] bg-card p-6 text-left"
        >
          <p className="mb-4 text-[10px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground">
            Método de pago
          </p>
          <p className="text-sm font-semibold text-foreground">
            {order.payment_method
              ? PAYMENT_METHOD_LABELS[order.payment_method]
              : 'No especificado'}
          </p>
        </motion.div>

        {isGuest && (
          <motion.div
            initial={prefersReduced ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={prefersReduced ? { duration: 0 } : { delay: 0.52 }}
            className="mb-5 rounded-2xl border border-neon-cyan/20 bg-neon-cyan/10 p-4 text-left"
          >
            <p className="mb-3 text-xs leading-relaxed text-neon-cyan">
              <strong>¿Quieres seguir tu pedido más fácil?</strong> Crea una
              cuenta con el mismo email para tener todos tus pedidos en un solo
              lugar.
            </p>
            <Link
              to={`/register?email=${encodeURIComponent(order.guest_email ?? '')}`}
              className="block rounded-lg bg-neon-cyan px-4 py-2 text-center text-xs font-bold uppercase tracking-wide text-background transition hover:bg-neon-cyan/90"
            >
              Crear cuenta
            </Link>
          </motion.div>
        )}

        {!isCancelled && (
        <motion.div
          initial={prefersReduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.55 }}
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
        )}

        <motion.button
          initial={prefersReduced ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.6 }}
          type="button"
          onClick={handleGoHome}
          className="w-full rounded-xl py-4 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </motion.button>

        {!isCancelled && (
        <motion.div
          initial={prefersReduced ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={prefersReduced ? { duration: 0 } : { delay: 0.7 }}
          className="mt-4 space-y-3"
        >
          <Link
            to={`/order/${order.order_number}`}
            className="block w-full rounded-xl border border-neon-cyan/40 bg-transparent py-3.5 text-center text-sm font-bold uppercase tracking-wide text-neon-cyan transition-all hover:border-neon-cyan hover:bg-neon-cyan/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan"
          >
            Rastrear mi pedido
          </Link>
          {isAuthenticated && !isGuest && (
            <Link
              to={`/orders?new=${order.order_number}`}
              className="block w-full rounded-xl border border-neon-magenta-500/40 bg-transparent py-3.5 text-center text-sm font-bold uppercase tracking-wide text-neon-magenta-500 transition-all hover:border-neon-magenta-500 hover:bg-neon-magenta-500/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-magenta-500"
            >
              Mis pedidos
            </Link>
          )}
        </motion.div>
        )}
      </motion.div>
    </main>
  )
}
