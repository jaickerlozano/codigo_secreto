import { format } from 'date-fns'
import { es } from 'date-fns/locale'

import { formatCLP } from '@/lib/format'
import type { components } from '@/api/schema.d.ts'

type OrderStatus = components['schemas']['OrderStatusEnum']

const STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING: 'Pendiente de pago',
  PAID: 'Pagado / Listo para despacho',
  SHIPPED: 'Enviado a destino',
  DELIVERED: 'Entregado',
  CANCELLED: 'Cancelado',
}

export function parseNewOrderParam(params: URLSearchParams): string | undefined {
  const raw = params.get('new')
  if (!raw || raw.length > 20 || !/^CS-[A-Z0-9]+$/.test(raw)) return undefined
  return raw
}

export function getOrderStatusLabel(status: OrderStatus): string {
  return STATUS_LABELS[status]
}

export function formatOrderDate(isoDate: string): string {
  return format(new Date(isoDate), "d 'de' MMMM 'de' yyyy", { locale: es })
}

export function formatOrderTotal(total: number): string {
  return formatCLP(total)
}

export function getOrderTrackingHref(orderNumber: string): string {
  return `/order/${orderNumber}`
}
