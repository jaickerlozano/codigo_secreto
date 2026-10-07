import { useEffect, useState } from 'react'
import type { QueryClient } from '@tanstack/react-query'

import type { Order } from '../api/orders.api'

export type PaymentHoldState = 'active' | 'expired' | 'unknown' | 'terminal'
type HoldOrder = Pick<Order, 'status' | 'payment_expires_at' | 'cancellation_reason'>

export function getPaymentHoldState(order: HoldOrder, now = Date.now()): PaymentHoldState {
  if (order.status !== 'PENDING') return 'terminal'
  const deadline = order.payment_expires_at ? Date.parse(order.payment_expires_at) : NaN
  if (!Number.isFinite(deadline)) return 'unknown'
  return deadline > now ? 'active' : 'expired'
}

// Display validity, not a scarcity countdown. The backend still validates every mutation.
export function usePaymentHoldState(order: HoldOrder | null | undefined): PaymentHoldState {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const deadline = order?.payment_expires_at ? Date.parse(order.payment_expires_at) : NaN
    if (order?.status !== 'PENDING' || !Number.isFinite(deadline)) return
    const delay = deadline - Date.now()
    if (delay <= 0) return
    const timer = window.setTimeout(() => setNow(Date.now()), Math.min(delay, 2_147_483_647))
    return () => window.clearTimeout(timer)
  }, [order?.status, order?.payment_expires_at, now])
  return order ? getPaymentHoldState(order, Math.max(now, Date.now())) : 'unknown'
}

export function formatPaymentDeadline(deadline: string): string {
  return new Date(deadline).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' })
}

const actorScopes = new WeakMap<QueryClient, { actor: string; generation: number }>()

// A new in-memory scope on every actor transition prevents A → guest → A cache reuse.
// Keys carry neither customer details nor cookie/capability material.
export function pendingOrderScope(client: QueryClient, actor: string) {
  const previous = actorScopes.get(client)
  const changed = previous !== undefined && previous.actor !== actor
  const generation = previous ? previous.generation + (changed ? 1 : 0) : 0
  actorScopes.set(client, { actor, generation })
  return { generation, changed }
}

export async function invalidateOrderWorkflow(client: QueryClient): Promise<void> {
  await Promise.all(['pending-order', 'orders', 'order', 'products', 'product', 'cart', 'guest-quote', 'dispatch-options'].map(
    (key) => client.invalidateQueries({ queryKey: [key] }),
  ))
}
