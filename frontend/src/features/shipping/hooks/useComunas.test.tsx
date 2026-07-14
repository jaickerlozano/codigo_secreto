import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useComunas } from './useComunas'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useComunas', () => {
  it('returns all comunas when no region is provided', async () => {
    const { result } = renderHook(() => useComunas(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(3)
  })

  it('returns comunas filtered by region', async () => {
    const { result } = renderHook(() => useComunas(13), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.map((c) => c.name)).toEqual([
      'Santiago',
      'Providencia',
    ])
  })

  it('stays disabled when enabled is false', async () => {
    const { result } = renderHook(
      () => useComunas(undefined, { enabled: false }),
      { wrapper: Wrapper },
    )

    expect(result.current.isPending).toBe(true)
    expect(result.current.fetchStatus).toBe('idle')
  })
})
