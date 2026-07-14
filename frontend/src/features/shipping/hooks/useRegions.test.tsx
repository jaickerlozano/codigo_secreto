import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useRegions } from './useRegions'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useRegions', () => {
  it('returns the list of regions', async () => {
    const { result } = renderHook(() => useRegions(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0].name).toBe('Región Metropolitana')
    expect(result.current.data?.[0].id).toBe(13)
  })

  it('returns an error when the request fails', async () => {
    server.use(
      http.get('*api/shipping/regions/', () =>
        HttpResponse.json({ detail: 'Error del servidor' }, { status: 500 }),
      ),
    )

    const { result } = renderHook(() => useRegions(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true), {
      timeout: 3000,
    })
    expect(result.current.error?.message).toBe(
      'Error del servidor. Intenta más tarde.',
    )
  })
})
