import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useCartItems } from './useCartItems'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useCartItems', () => {
  it('returns the authenticated cart when enabled', async () => {
    const { result } = renderHook(
      () => useCartItems({ enabled: true }),
      { wrapper: Wrapper },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toEqual([])
  })

  it('does not fetch when disabled', async () => {
    const { result } = renderHook(
      () => useCartItems({ enabled: false }),
      { wrapper: Wrapper },
    )

    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})
