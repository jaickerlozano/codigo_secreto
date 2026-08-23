import { Truck } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { components } from '@/api/schema.d.ts'

import { useOrders } from '../hooks/useOrders'
import { formatOrderDate, formatOrderTotal, getOrderStatusLabel, getOrderTrackingHref, parseNewOrderParam } from '../lib/mappers'

type Order = components['schemas']['Order']

const badgeClass = (status: Order['status']) =>
  status === 'CANCELLED' ? 'bg-error-500/10 text-error-500' : status === 'DELIVERED' ? 'bg-neon-lime/10 text-neon-lime' : 'bg-neon-cyan/10 text-neon-cyan'

export function OrdersPage() {
  const [searchParams] = useSearchParams()
  const highlighted = parseNewOrderParam(searchParams)
  const { data, isLoading, isError, refetch } = useOrders()

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12" role="status">
        <Skeleton className="mb-8 h-8 w-48" />
        <div className="space-y-4"><Skeleton className="h-40 w-full" /></div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <main id="main-content" className="min-h-screen px-4 py-16">
        <Alert variant="destructive" className="mx-auto max-w-3xl">
          <AlertTitle>No se pudieron cargar los pedidos</AlertTitle>
          <AlertDescription className="flex flex-col gap-4">
            <span>Hubo un problema al obtener tu historial. Inténtalo de nuevo.</span>
            <Button type="button" variant="outline" size="sm" onClick={() => void refetch()}>Reintentar</Button>
          </AlertDescription>
        </Alert>
      </main>
    )
  }

  return (
    <main id="main-content" className="min-h-screen px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-extrabold uppercase tracking-wide text-foreground sm:text-3xl">Mis pedidos</h1>
        {data.results.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.06] bg-card px-6 py-16 text-center">
            <h2 className="mb-2 text-lg font-semibold text-foreground">Aún no tienes pedidos</h2>
            <p className="text-sm text-muted-foreground">Cuando realices una compra, tus pedidos aparecerán aquí.</p>
          </div>
        ) : (
          <ul className="space-y-5">
            {data.results.map((order) => {
              const isHighlighted = order.order_number === highlighted
              return (
                <li key={order.id}>
                  <article data-highlighted={isHighlighted} className={`relative rounded-2xl border bg-card p-5 ${isHighlighted ? 'border-neon-magenta/60 shadow-[0_0_0_1px_var(--color-neon-magenta)]' : 'border-white/[0.06]'}`}>
                    {isHighlighted && <span className="absolute -top-2 left-4 rounded-full bg-neon-magenta px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-background">Pedido recién realizado</span>}
                    <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Número de pedido</p>
                        <p className="font-mono text-lg font-extrabold text-foreground">{order.order_number}</p>
                      </div>
                      <span className={`w-fit rounded-full px-2.5 py-1 text-xs font-bold ${badgeClass(order.status)}`}>{getOrderStatusLabel(order.status)}</span>
                    </div>
                    <p className="mb-4 text-sm text-foreground">{formatOrderDate(order.created_at)} · <span className="font-semibold">{formatOrderTotal(order.total)}</span></p>
                    <Link to={getOrderTrackingHref(order.order_number)} className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-neon-cyan/40 px-4 py-2 text-sm font-bold uppercase tracking-wide text-neon-cyan transition-all hover:border-neon-cyan hover:bg-neon-cyan/8 focus-visible:ring-2 focus-visible:ring-neon-cyan"><Truck size={16} aria-hidden="true" /> Rastrear pedido</Link>
                  </article>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </main>
  )
}
