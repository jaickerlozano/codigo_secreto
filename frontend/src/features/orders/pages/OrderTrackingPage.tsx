import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { motion } from 'motion/react'
import {
  ArrowLeft,
  Box,
  CreditCard,
  MapPin,
  MessageCircle,
  PackageX,
  Phone,
} from 'lucide-react'

import type { Product } from '@/features/catalog/types'
import { formatCLP } from '@/lib/format'

import {
  OrderTimeline,
  type TimelineStep,
} from '../components/OrderTimeline'

const ORDER_STORAGE_KEY = 'cs-last-order'
const SUPPORT_PHONE = '56912345678'

const MOCK_PRODUCTS: Product[] = [
  {
    id: 1,
    name: 'Vibrador Luna Pro',
    price: 29990,
    category: 'Vibradores',
    experienceLevel: 'principiante',
    features: ['10 modos'],
    description: 'Vibrador de prueba',
    materials: ['Silicona'],
    usageInstructions: 'Instrucciones de prueba',
    icon: '✦',
    gradient: 'from-violet-950 via-purple-900 to-violet-800',
    sku: '101',
    stock: 10,
    image: null,
  },
  {
    id: 3,
    name: 'Lubricante Sensorial',
    price: 12990,
    category: 'Lubricantes',
    experienceLevel: 'principiante',
    features: ['Base agua'],
    description: 'Lubricante de prueba',
    materials: ['Base agua'],
    usageInstructions: 'Instrucciones de prueba',
    icon: '◈',
    gradient: 'from-cyan-950 via-teal-900 to-cyan-800',
    sku: '301',
    stock: 20,
    image: null,
  },
]

const MOCK_ORDER = {
  number: 'CS-123456',
  createdAt: '03 jul 2026, 10:30',
  currentStepIndex: 1,
  carrier: 'Chilexpress',
  trackingNumber: 'CHX-9988776655',
  shipping: {
    name: 'Valentina G.',
    address: 'Av. Providencia 1234, Dpto 502',
    city: 'Providencia, Santiago',
    phone: '+56 9 1234 5678',
  },
  payment: {
    method: 'Webpay / Tarjeta bancaria',
    last4: '**** 4242',
  },
  items: [
    { product: MOCK_PRODUCTS[0], quantity: 1 },
    { product: MOCK_PRODUCTS[1], quantity: 2 },
  ],
  shippingCost: 3490,
}

function buildTimeline(
  currentStepIndex: number,
  carrier: string,
  trackingNumber: string,
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
      timestamp: '03 jul 2026, 11:15',
      completed: currentStepIndex >= 2,
      current: currentStepIndex === 1,
    },
    {
      id: 'shipped',
      title: 'En camino',
      description: `Transporte: ${carrier}. N° de seguimiento: ${trackingNumber}.`,
      completed: currentStepIndex >= 3,
      current: currentStepIndex === 2,
    },
    {
      id: 'delivered',
      title: 'Entregado',
      description: 'Entrega confirmada en la dirección indicada.',
      completed: currentStepIndex >= 4,
      current: currentStepIndex === 3,
    },
  ]
}

export function OrderTrackingPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const [storedOrder, setStoredOrder] = useState<string | null>(null)

  useEffect(() => {
    setStoredOrder(sessionStorage.getItem(ORDER_STORAGE_KEY))
  }, [])

  const isValidOrder =
    !storedOrder || storedOrder === orderId || orderId === MOCK_ORDER.number

  const order = useMemo(
    () => ({
      ...MOCK_ORDER,
      number: orderId ?? MOCK_ORDER.number,
    }),
    [orderId],
  )

  const timeline = useMemo(
    () =>
      buildTimeline(
        order.currentStepIndex,
        order.carrier,
        order.trackingNumber,
        order.createdAt,
      ),
    [order],
  )

  const subtotal = useMemo(
    () =>
      order.items.reduce(
        (sum, item) => sum + item.product.price * item.quantity,
        0,
      ),
    [order.items],
  )

  const total = subtotal + order.shippingCost

  const handleContactSupport = () => {
    const message = `Hola, quisiera consultar sobre mi pedido ${order.number}`
    const href = `https://wa.me/${SUPPORT_PHONE}?text=${encodeURIComponent(message)}`
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  if (!isValidOrder) {
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
          No pudimos encontrar el pedido {orderId} en nuestro sistema.
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
            {order.number}
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
                    key={item.product.id}
                    className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0"
                  >
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        {item.product.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.quantity}{' '}
                        {item.quantity === 1 ? 'unidad' : 'unidades'}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-foreground">
                      {formatCLP(item.product.price * item.quantity)}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="mt-5 space-y-2 border-t border-border pt-4">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Subtotal</span>
                  <span>{formatCLP(subtotal)}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Envío ({order.carrier})</span>
                  <span>{formatCLP(order.shippingCost)}</span>
                </div>
                <div className="flex justify-between text-sm font-bold text-foreground">
                  <span>Total</span>
                  <span>{formatCLP(total)}</span>
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
                  {order.shipping.name}
                </p>
                <p className="text-muted-foreground">
                  {order.shipping.address}
                </p>
                <p className="text-muted-foreground">{order.shipping.city}</p>
                <p className="flex items-center gap-1.5 text-muted-foreground">
                  <Phone size={12} />
                  {order.shipping.phone}
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
                {order.payment.method}
              </p>
              <p className="text-xs text-muted-foreground">
                {order.payment.last4}
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
