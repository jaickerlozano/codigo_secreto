import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'
import { testOrder } from '@/test/handlers/orders'
import { useCancelOrder } from './useCancelOrder'

function setup() {
  const client = queryClient()
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
  return { client, ...renderHook(() => useCancelOrder(), { wrapper: Wrapper }) }
}

describe('useCancelOrder', () => {
  it('updates the generated order detail and invalidates pending/availability caches', async () => {
    server.use(http.post('http://localhost:8000/api/orders/by-order-number/CS-HOOK/cancel/', () => HttpResponse.json({ ...testOrder, order_number: 'CS-HOOK', status: 'CANCELLED', cancellation_reason: 'BUYER' })))
    const { client, result } = setup()
    client.setQueryData(['pending-order', 1], testOrder)
    client.setQueryData(['products'], [])
    act(() => result.current.mutate('CS-HOOK'))
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(client.getQueryData(['order', 'CS-HOOK'])).toMatchObject({ status: 'CANCELLED', cancellation_reason: 'BUYER' })
    expect(client.getQueryState(['pending-order', 1])?.isInvalidated).toBe(true)
    expect(client.getQueryState(['products'])?.isInvalidated).toBe(true)
  })
  it('invalidates after a stale conflict without fabricating a cancelled state', async () => {
    server.use(http.post('http://localhost:8000/api/orders/by-order-number/CS-HOOK/cancel/', () => HttpResponse.json({ detail: 'Estado cambiado' }, { status: 409 })))
    const { client, result } = setup()
    client.setQueryData(['order', 'CS-HOOK'], { ...testOrder, status: 'PAID' })
    act(() => result.current.mutate('CS-HOOK'))
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(client.getQueryState(['order', 'CS-HOOK'])?.isInvalidated).toBe(true)
    expect(client.getQueryData(['order', 'CS-HOOK'])).toMatchObject({ status: 'PAID' })
  })
})
