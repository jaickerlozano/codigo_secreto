import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse, delay } from 'msw'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'
import { testOrder } from '@/test/handlers/orders'
import { testUser } from '@/test/handlers/auth'
import { usePendingOrder } from './usePendingOrder'

function setup() {
  const client = queryClient()
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}><AuthProvider>{children}</AuthProvider></QueryClientProvider>
  }
  return { client, ...renderHook(() => usePendingOrder(), { wrapper: Wrapper }) }
}

describe('usePendingOrder', () => {
  it('waits for auth and resolves 204 to null', async () => {
    const { result } = setup()
    expect(result.current.data).toBeUndefined()
    expect(result.current.isDiscovering).toBe(true)
    await waitFor(() => expect(result.current.isResolved).toBe(true))
    expect(result.current.data).toBeNull()
  })
  it('cancels an old actor request so a late response cannot repopulate recovery', async () => {
    let firstRequest: Request | undefined
    let release: () => void = () => {}
    const oldResponse = new Promise<void>(resolve => { release = resolve })
    server.use(http.get('http://localhost:8000/api/orders/pending/', async ({ request }) => {
      if (!firstRequest) {
        firstRequest = request
        await oldResponse
        return HttpResponse.json({ ...testOrder, order_number: 'CS-OLD' })
      }
      return HttpResponse.json({ ...testOrder, order_number: 'CS-NEW' })
    }))
    const { client, result } = setup()
    try {
      await waitFor(() => expect(firstRequest).toBeDefined())
      act(() => client.setQueryData(['me'], { ...testUser, id: 2 }))
      await waitFor(() => expect(result.current.data?.order_number).toBe('CS-NEW'))
      expect(firstRequest?.signal.aborted).toBe(true)
      expect(client.getQueriesData({ queryKey: ['pending-order'] })).toHaveLength(1)
    } finally { release() }
  })
  it('cleans old actor caches and never flashes another account or a previous guest order', async () => {
    let number = 'CS-A'
    server.use(http.get('http://localhost:8000/api/orders/pending/', async () => {
      const captured = number
      await delay(100)
      return HttpResponse.json({ ...testOrder, order_number: captured })
    }))
    const { result, client } = setup()
    await waitFor(() => expect(result.current.data?.order_number).toBe('CS-A'))
    number = 'CS-B'
    act(() => client.setQueryData(['me'], { ...testUser, id: 2, email: 'b@example.com' }))
    await waitFor(() => expect(result.current.data).toBeUndefined(), { interval: 1 })
    expect(client.getQueriesData({ queryKey: ['pending-order'] }).some(([, data]) => JSON.stringify(data)?.includes('CS-A'))).toBe(false)
    await waitFor(() => expect(result.current.data?.order_number).toBe('CS-B'))
    number = 'CS-GUEST'
    act(() => client.setQueryData(['me'], null))
    await waitFor(() => expect(result.current.data).toBeUndefined(), { interval: 1 })
    await waitFor(() => expect(result.current.data?.order_number).toBe('CS-GUEST'))
    number = 'CS-A-NEW'
    act(() => client.setQueryData(['me'], testUser))
    await waitFor(() => expect(result.current.data).toBeUndefined(), { interval: 1 })
    await waitFor(() => expect(result.current.data?.order_number).toBe('CS-A-NEW'))
    expect(client.getQueriesData({ queryKey: ['pending-order'] })).toHaveLength(1)
    const keys = JSON.stringify(client.getQueryCache().getAll().filter(q => q.queryKey[0] === 'pending-order').map(q => q.queryKey))
    expect(keys).not.toContain('example.com')
    expect(keys).not.toContain('user:')
    expect(keys).not.toContain('CS-')
  })
})
