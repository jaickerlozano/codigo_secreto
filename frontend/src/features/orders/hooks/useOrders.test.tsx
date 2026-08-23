import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useOrders } from './useOrders'

function Wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
}

const listResponse = (results: unknown[]) => ({ count: results.length, next: null, previous: null, results })

describe('useOrders', () => {
  it('requests page 1 of the authenticated order list', async () => {
    let requestedPage: string | null = null
    server.use(http.get('http://localhost:8000/api/orders/', ({ request }) => {
      requestedPage = new URL(request.url).searchParams.get('page')
      return HttpResponse.json(listResponse([{ id: 1, order_number: 'CS-1001', status: 'PAID', total: 29990, created_at: '2026-07-14T10:30:00Z' }]))
    }))
    const { result } = renderHook(() => useOrders(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(requestedPage).toBe('1')
    expect(result.current.data?.results[0].order_number).toBe('CS-1001')
  })

  it('exposes loading and error states', async () => {
    server.use(http.get('http://localhost:8000/api/orders/', () => HttpResponse.json({ detail: 'Error' }, { status: 500 })))
    const { result } = renderHook(() => useOrders(), { wrapper: Wrapper })
    expect(result.current.isLoading).toBe(true)
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 3000 })
    expect(result.current.error).toBeDefined()
  })

  it('refetches when the refetch helper is invoked', async () => {
    let calls = 0
    server.use(http.get('http://localhost:8000/api/orders/', () => HttpResponse.json(listResponse([{ id: ++calls, order_number: `CS-${1000 + calls}`, status: 'PAID', total: 29990, created_at: '2026-07-14T10:30:00Z' }]))))
    const { result } = renderHook(() => useOrders(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.results[0].order_number).toBe('CS-1001')
    result.current.refetch()
    await waitFor(() => expect(result.current.data?.results[0].order_number).toBe('CS-1002'))
  })
})
