import { Link, useLocation, useParams } from 'react-router'
import { motion } from 'motion/react'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Box,
  CreditCard,
  MapPin,
  MessageCircle,
  PackageX,
  Phone,
} from 'lucide-react'

import { formatCLP } from '@/lib/format'
import { SUPPORT_PHONE } from '@/lib/config'
import type { components } from '@/api/schema.d.ts'

import { useOrder } from '../hooks/useOrder'
import { OrderTimeline, type TimelineStep } from '../components/OrderTimeline'
import { exchangeOrderAccessFromLocation } from '../api/orders.api'

type OrderStatus = components['schemas']['StatusEnum']
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

function buildTimeline(
  status: OrderStatus,
  createdAt: string,
  carrier: string,
  trackingNumber: string | null,
): TimelineStep[] {
  const cancelled = status === 'CANCELLED'

  const steps: TimelineStep[] = [
    {
      id: 'received',
      title: 'Pedido recibido',
      description: cancelled
        ? 'El pedido fue recibido pero posteriormente cancelado.'
        : 'Tu pedido fue confirmado y está en nuestro sistema.',
      timestamp: new Date(createdAt).toLocaleString('es-CL'),
      completed: true,
      current: status === 'PENDING',
    },
    {
      id: 'preparing',
      title: 'Preparando',
      description:
        'Estamos armando tu pedido con empaque 100% discreto y neutro.',
      completed: status === 'PAID' || status === 'SHIPPED' || status === 'DELIVERED',
      current: status === 'PAID',
    },
    {
      id: 'shipped',
      title: 'En camino',
      description: trackingNumber
        ? `Transporte: ${carrier}. N° de seguimiento: ${trackingNumber}.`
        : `Transporte: ${carrier}.`,
      completed: status === 'SHIPPED' || status === 'DELIVERED',
      current: status === 'SHIPPED',
    },
    {
      id: 'delivered',
      title: 'Entregado',
      description: 'Entrega confirmada en la dirección indicada.',
      completed: status === 'DELIVERED',
      current: status === 'DELIVERED',
    },
  ]

  if (cancelled) {
    steps.push({
      id: 'cancelled',
      title: 'Cancelado',
      description: 'Este pedido fue cancelado.',
      completed: true,
      current: true,
    })
  }

  return steps
}

export function OrderTrackingPage() {
  const { orderId: paramOrderId } = useParams<{ orderId: string }>()
  const location = useLocation()
  const orderNumber = paramOrderId || undefined
  const accessQuery = useQuery({
    queryKey: ['order-access', orderNumber, location.hash],
    queryFn: () =>
      exchangeOrderAccessFromLocation(
        orderNumber!,
        location,
        globalThis.history,
      ),
    enabled: Boolean(orderNumber && location.hash),
    retry: false,
  })
  const accessReady = !location.hash || accessQuery.isSuccess
  const { data: order, isLoading: isOrderLoading, error } = useOrder(accessReady ? orderNumber : undefined)

  const handleContactSupport = () => {
    if (!order) return
    const message = `Hola, quisiera consultar sobre mi pedido ${order.order_number}`
    const href = `https://wa.me/${SUPPORT_PHONE}?text=${encodeURIComponent(message)}`
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  if (!orderNumber || accessQuery.isError) {
    return (
      <main
        id="main-content"
        className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-20 text-center"
      >
        <PackageX size={48} className="mb-4 text-muted-foreground" />
        <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">
          Pedido no encontrado
        </h1>
        <p className="mb-6 max-w-xs text-sm text-muted-foreground">
          No pudimos encontrar el pedido en nuestro sistema.
        </p>
        <Link
          to="/"
          className="flex min-h-12 items-center justify-center rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </Link>
      </main>
    )
  }

  if ((location.hash && accessQuery.isPending) || isOrderLoading) {
    return (
      <main id="main-content" className="min-h-[60vh] px-4 py-20">
        <TrackingSkeleton />
      </main>
    )
  }

  if (error || !order) {
    return (
      <main
        id="main-content"
        className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-20 text-center"
        role="alert"
      >
        <PackageX size={48} className="mb-4 text-muted-foreground" />
        <h1 className="mb-2 text-2xl font-extrabold uppercase tracking-wide text-foreground">
          Pedido no encontrado
        </h1>
        <p className="mb-6 max-w-xs text-sm text-muted-foreground">
          {error?.message ||
            `No pudimos encontrar el pedido ${orderNumber} en nuestro sistema.`}
        </p>
        <Link
          to="/"
          className="flex min-h-12 items-center justify-center rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </Link>
      </main>
    )
  }

  const timeline = buildTimeline(
    order.status,
    order.created_at,
    order.carrier,
    order.tracking_number,
  )

  return (
    <main id="main-content" className="px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-6"
        >
          <Link
            to="/"
            className="mb-4 inline-flex min-h-12 items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ArrowLeft size={14} /> Volver al inicio
          </Link>
          <h1 className="text-2xl font-extrabold uppercase tracking-wide text-foreground sm:text-3xl">
            Seguimiento de pedido
          </h1>
          <p className="mt-1 font-mono text-sm text-neon-magenta">
            {order.order_number}
          </p>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="rounded-2xl border border-border bg-card p-6"
            aria-label="Timeline del pedido"
          >
            <h2 className="mb-6 text-sm font-bold uppercase tracking-wide text-foreground">
              Estado del pedido
            </h2>
            <OrderTimeline steps={timeline} />
          </motion.section>

          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="rounded-2xl border border-border bg-card p-6"
            >
              <h2 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-foreground">
                <Box size={14} className="text-neon-cyan" />
                Productos
              </h2>
              <ul className="space-y-4">
                {order.items.map((item) => (
                  <li
                    key={item.id}
                    className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0"
                  >
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        {item.product_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.quantity}{' '}
                        {item.quantity === 1 ? 'unidad' : 'unidades'}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-foreground">
                      {formatCLP(item.subtotal)}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="mt-5 space-y-2 border-t border-border pt-4">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Subtotal</span>
                  <span>{formatCLP(order.subtotal)}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Envío ({order.carrier})</span>
                  <span>
                    {order.shipping_cost === 0
                      ? 'Gratis'
                      : formatCLP(order.shipping_cost)}
                  </span>
                </div>
                <div className="flex justify-between text-sm font-bold text-foreground">
                  <span>Total</span>
                  <span>{formatCLP(order.total)}</span>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="rounded-2xl border border-border bg-card p-6"
            >
              <h2 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-foreground">
                <MapPin size={14} className="text-neon-cyan" />
                Dirección de envío
              </h2>
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
                <p className="flex items-center gap-1.5 text-muted-foreground">
                  <Phone size={12} />
                  {order.phone}
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.35 }}
              className="rounded-2xl border border-border bg-card p-6"
            >
              <h2 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-foreground">
                <CreditCard size={14} className="text-neon-cyan" />
                Método de pago
              </h2>
              <p className="text-sm font-semibold text-foreground">
                {order.payment_method
                  ? PAYMENT_METHOD_LABELS[order.payment_method]
                  : 'No especificado'}
              </p>
              <p className="text-xs text-muted-foreground">
                {STATUS_LABELS[order.status]}
              </p>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              type="button"
              onClick={handleContactSupport}
              className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-neon-lime/30 bg-neon-lime/10 py-3.5 text-sm font-bold uppercase tracking-wide text-neon-lime transition-all hover:bg-neon-lime/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-lime"
            >
              <MessageCircle size={16} />
              Contactar soporte
            </motion.button>
          </div>
        </div>
      </div>
    </main>
  )
}
function TrackingSkeleton() {
  return <div role="status" aria-label="Cargando seguimiento del pedido" className="mx-auto max-w-5xl animate-pulse"><div className="mb-6 h-8 w-64 rounded bg-muted" aria-hidden="true" /><div className="h-72 rounded-2xl border border-border bg-card" /></div>
}
