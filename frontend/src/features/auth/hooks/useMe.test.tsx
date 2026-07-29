import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useMe } from './useMe'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useMe', () => {
  it('returns the current user when authenticated', async () => {
    server.use(
       http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          rut: null,
          phone: null,
          is_admin: false,
        }),
      ),
    )

    const { result } = renderHook(() => useMe(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.email).toBe('test@example.com')
  })

  it('returns null when the user is not authenticated', async () => {
    server.use(
       http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({ detail: 'No autenticado' }, { status: 401 }),
      ),
    )

    const { result } = renderHook(() => useMe(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
  })
})
