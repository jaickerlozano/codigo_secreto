import { describe, expect, it } from 'vitest'

import { formatOrderDate, formatOrderTotal, getOrderStatusLabel, getOrderTrackingHref, parseNewOrderParam } from './mappers'

describe('parseNewOrderParam', () => {
  it('accepts valid CS- uppercase alphanumeric values up to max length', () => {
    expect(parseNewOrderParam(new URLSearchParams('new=CS-1001'))).toBe('CS-1001')
    expect(parseNewOrderParam(new URLSearchParams('new=CS-12345678901234567'))).toBe('CS-12345678901234567')
  })

  it('returns undefined for missing, empty, or malformed values', () => {
    expect(parseNewOrderParam(new URLSearchParams())).toBeUndefined()
    expect(parseNewOrderParam(new URLSearchParams('new='))).toBeUndefined()
    expect(parseNewOrderParam(new URLSearchParams('new=cs-1001'))).toBeUndefined()
    expect(parseNewOrderParam(new URLSearchParams('new=ORD-1001'))).toBeUndefined()
    expect(parseNewOrderParam(new URLSearchParams('new=CS-1001<script>'))).toBeUndefined()
    expect(parseNewOrderParam(new URLSearchParams('new=CS-123456789012345678'))).toBeUndefined()
  })

  it('uses only the first value when repeated', () => {
    expect(parseNewOrderParam(new URLSearchParams('new=CS-1001&new=CS-1002'))).toBe('CS-1001')
  })
})

describe('order presentation helpers', () => {
  it('maps every generated status to a label', () => {
    expect(getOrderStatusLabel('PENDING')).toBe('Pendiente de pago')
    expect(getOrderStatusLabel('PAID')).toBe('Pagado / Listo para despacho')
    expect(getOrderStatusLabel('SHIPPED')).toBe('Enviado a destino')
    expect(getOrderStatusLabel('DELIVERED')).toBe('Entregado')
    expect(getOrderStatusLabel('CANCELLED')).toBe('Cancelado')
  })

  it('formats backend values without calculating them', () => {
    expect(formatOrderDate('2026-07-14T10:30:00Z')).toBe('14 de julio de 2026')
    expect(formatOrderTotal(29990)).toBe('$29.990')
  })

  it('returns the tracking href for an order number', () => {
    expect(getOrderTrackingHref('CS-1001')).toBe('/order/CS-1001')
  })
})
