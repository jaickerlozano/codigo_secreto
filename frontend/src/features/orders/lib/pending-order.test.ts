import { describe, expect, it, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { QueryClient } from '@tanstack/react-query'
import { getPaymentHoldState, invalidateOrderWorkflow, pendingOrderScope, usePaymentHoldState } from './pending-order'
import { testOrder } from '@/test/handlers/orders'

const now = Date.parse('2026-01-01T00:00:00Z')
describe('server hold display', () => {
  it.each([
    ['PENDING', '2026-01-01T00:00:01Z', 'active'],
    ['PENDING', '2026-01-01T00:00:00Z', 'expired'],
    ['PENDING', '2025-12-31T23:59:59Z', 'expired'],
    ['PENDING', null, 'unknown'],
    ['PENDING', 'invalid', 'unknown'],
    ['PAID', '2026-01-01T00:00:01Z', 'terminal'],
    ['CANCELLED', '2026-01-01T00:00:01Z', 'terminal'],
  ] as const)('%s / %s is %s', (status, payment_expires_at, expected) => {
    expect(getPaymentHoldState({ ...testOrder, status, payment_expires_at }, now)).toBe(expected)
  })
  it('changes validity at the actual deadline without a countdown or mutation', () => {
    vi.useFakeTimers()
    vi.setSystemTime(now)
    try {
      const order = { ...testOrder, payment_expires_at: '2026-01-01T00:00:01Z' }
      const { result } = renderHook(() => usePaymentHoldState(order))
      expect(result.current).toBe('active')
      act(() => vi.advanceTimersByTime(1000))
      expect(result.current).toBe('expired')
    } finally { vi.useRealTimers() }
  })
  it('does not reuse an actor cache across guest/account transitions', () => {
    const client = new QueryClient()
    expect(pendingOrderScope(client, 'guest').generation).toBe(0)
    expect(pendingOrderScope(client, 'account-A').generation).toBe(1)
    expect(pendingOrderScope(client, 'account-B').generation).toBe(2)
    expect(pendingOrderScope(client, 'guest').generation).toBe(3)
    expect(pendingOrderScope(client, 'account-A').generation).toBe(4)
  })
  it('invalidates order, recovery, availability and quote/cart caches', async () => {
    const client = new QueryClient()
    const keys = ['pending-order', 'order', 'orders', 'products', 'product', 'cart', 'guest-quote', 'dispatch-options']
    keys.forEach(key => client.setQueryData([key], 'cached'))
    await invalidateOrderWorkflow(client)
    keys.forEach(key => expect(client.getQueryState([key])?.isInvalidated).toBe(true))
  })
})
