import { Link, useLocation } from 'react-router'
import { Skeleton } from '@/components/ui/skeleton'

import { usePendingOrder } from '../hooks/usePendingOrder'
import { formatPaymentDeadline, usePaymentHoldState } from '../lib/pending-order'

const control = 'inline-flex min-h-12 items-center rounded-lg border border-neon-cyan/50 px-4 py-3 text-base-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan'

export function PendingOrderNotice() {
  const pending = usePendingOrder()
  const location = useLocation()
  const order = pending.data
  const hold = usePaymentHoldState(order)
  // Auth resolution is shared with page-level loading/errors. Keep this visible,
  // but don't duplicate their interruptive announcements before discovery starts.
  if (pending.isAuthLoading) return (
    <section aria-label="Preparando consulta de pedidos" aria-busy="true" className="mx-auto w-full max-w-5xl px-4 py-3">
      <Skeleton className="h-12 w-full" />
    </section>
  )
  if (pending.isDiscovering) return (
    <div role="status" aria-label="Buscando pedido pendiente" className="mx-auto w-full max-w-5xl px-4 py-3">
      <Skeleton className="h-12 w-full" /><span className="sr-only">Buscando pedido pendiente…</span>
    </div>
  )
  if (pending.discoveryError) return (
    <section aria-label="Recuperar pedido" aria-live={pending.authError ? 'polite' : undefined} className="mx-auto w-full max-w-5xl px-4 py-3">
      <p role={pending.authError ? undefined : 'alert'} className="text-base-100">{pending.authError ? 'No pudimos verificar tu sesión para consultar pedidos.' : 'No pudimos consultar tu pedido pendiente.'} {pending.discoveryError.message}</p>
      <button type="button" className={control} onClick={() => void pending.retryDiscovery()}>Reintentar consulta</button>
    </section>
  )
  if (!order || order.status !== 'PENDING') return null
  if ([`/checkout/payment/${order.order_number}`, `/order/${order.order_number}`].includes(location.pathname)) return null
  return (
    <section aria-label="Pedido pendiente" className="mx-auto flex w-full max-w-5xl flex-col gap-3 rounded-xl border border-neon-cyan/30 bg-base-900 p-4 text-base-100 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p>Pedido {order.order_number} pendiente de pago</p>
        {hold === 'active' && order.payment_expires_at && <p>Pago disponible hasta <time dateTime={order.payment_expires_at}>{formatPaymentDeadline(order.payment_expires_at)}</time></p>}
        {hold === 'expired' && <p role="status">Plazo de pago vencido</p>}
        {hold === 'unknown' && <p role="status">No hay un plazo de pago válido. Revisa el pedido.</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {hold === 'active' && <Link to={`/checkout/payment/${order.order_number}`} className={control}>Continuar pago</Link>}
        <Link to={`/order/${order.order_number}`} className={control}>Ver pedido</Link>
      </div>
    </section>
  )
}
