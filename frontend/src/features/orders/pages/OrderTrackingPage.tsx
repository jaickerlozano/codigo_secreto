import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { motion } from 'motion/react'
import {
  ArrowLeft,
  Box,
  CreditCard,
  Loader2,
  MapPin,
  MessageCircle,
  PackageX,
  Phone,
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

import { formatCLP } from '@/lib/format'
import { SUPPORT_PHONE } from '@/lib/config'

import { useOrder } from '../hooks/useOrder'
import {
  OrderTimeline,
  type TimelineStep,
} from '../components/OrderTimeline'

const ORDER_STORAGE_KEY = 'cs-last-order'

const STATUS_TO_STEP_INDEX: Record<string, number> = {
  PENDING: 0,
  PAID: 1,
  SHIPPED: 2,
  DELIVERED: 3,
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  webpay: 'Webpay / Tarjeta bancaria',
  flow: 'Flow',
  mercadopago: 'MercadoPago',
  transfer: 'Transferencia Bancaria',
}

function buildTimeline(
  currentStepIndex: number,
  carrier: string,
  trackingNumber: string | null,
  createdAt: string,
): TimelineStep[] {
  return [
    {
      id: 'received',
      title: 'Pedido recibido',
      description: 'Tu pedido fue confirmado y está en nuestro sistema.',
      timestamp: createdAt,
      completed: currentStepIndex >= 0,
      current: currentStepIndex === 0,
    },
    {
      id: 'preparing',
      title: 'Preparando',
      description:
        'Estamos armando tu pedido con empaque 100% discreto y neutro.',
      timestamp: '',
      completed: currentStepIndex >= 2,
      current: currentStepIndex === 1,
    },
    {
      id: 'shipped',
      title: 'En camino',
      description: trackingNumber
        ? `Transporte: ${carrier}. N° de seguimiento: ${trackingNumber}.`
        : `Transporte: ${carrier}.`,
      timestamp: '',
      completed: currentStepIndex >= 3,
      current: currentStepIndex === 2,
    },
    {
      id: 'delivered',
      title: 'Entregado',
      description: 'Entrega confirmada en la dirección indicada.',
      timestamp: '',
      completed: currentStepIndex >= 4,
      current: currentStepIndex === 3,
    },
  ]
}

export function OrderTrackingPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const [storedOrderNumber, setStoredOrderNumber] = useState<string | null>(null)

  useEffect(() => {
    setStoredOrderNumber(sessionStorage.getItem(ORDER_STORAGE_KEY))
  }, [])

  const orderNumber = orderId ?? storedOrderNumber ?? undefined
  const { data: order, isLoading, error } = useOrder(orderNumber)

  const timeline = useMemo<TimelineStep[]>(() => {
    if (!order) {
      return []
    }

    const currentStepIndex = STATUS_TO_STEP_INDEX[order.status] ?? 0
    const createdAt = format(new Date(order.created_at), "dd MMM yyyy, HH:mm", {
      locale: es,
    })

    return buildTimeline(
      currentStepIndex,
      order.carrier,
      order.tracking_number,
      createdAt,
    )
  }, [order])

  const handleContactSupport = () => {
    const message = `Hola, quisiera consultar sobre mi pedido ${order?.order_number ?? orderNumber}`
    const href = `https://wa.me/${SUPPORT_PHONE}?text=${encodeURIComponent(message)}`
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  if (isLoading) {
    return (
      <main
        id="main-content"
        className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-20 text-center"
      >
        <Loader2 size={40} className="mb-4 animate-spin text-neon-magenta" />
        <p className="text-sm text-muted-foreground">Buscando tu pedido…</p>
      </main>
    )
  }

  if (!orderNumber) {
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
          No hay un número de pedido para consultar.
        </p>
        <Link
          to="/"
          className="rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </Link>
      </main>
    )
  }

  if (error || !order) {
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
          No pudimos encontrar el pedido {orderNumber} en nuestro sistema.
        </p>
        <Link
          to="/"
          className="rounded-xl px-6 py-3 text-sm font-bold uppercase tracking-wide text-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          style={{ background: 'var(--gradient-brand)' }}
        >
          Volver al inicio
        </Link>
      </main>
    )
  }

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
            className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-neon-magenta focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                  <span>{formatCLP(order.shipping_cost)}</span>
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
                  {order.guest_name ?? 'Cliente'}
                </p>
                <p className="text-muted-foreground">
                  {order.shipping_address}
                  {order.apartment_office ? `, ${order.apartment_office}` : ''}
                </p>
                <p className="text-muted-foreground">{order.comuna_display}</p>
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
                {PAYMENT_METHOD_LABELS[order.payment_method ?? 'webpay'] ??
                  'Webpay / Tarjeta bancaria'}
              </p>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              type="button"
              onClick={handleContactSupport}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-neon-lime/30 bg-neon-lime/10 py-3.5 text-sm font-bold uppercase tracking-wide text-neon-lime transition-all hover:bg-neon-lime/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-lime"
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
