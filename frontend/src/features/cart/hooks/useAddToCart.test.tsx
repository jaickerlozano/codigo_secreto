import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useAddToCart } from './useAddToCart'
import { useCartItems } from './useCartItems'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useAddToCart', () => {
  it('adds a product to the authenticated cart', async () => {
    const { result: mutation } = renderHook(() => useAddToCart(), {
      wrapper: Wrapper,
    })

    mutation.current.mutate({ product_id: 1, quantity: 2 })

    await waitFor(() => expect(mutation.current.isSuccess).toBe(true))

    const { result: query } = renderHook(
      () => useCartItems({ enabled: true }),
      { wrapper: Wrapper },
    )

    await waitFor(() => expect(query.current.isSuccess).toBe(true))
    expect(query.current.data?.items).toHaveLength(1)
    expect(query.current.data?.items[0].quantity).toBe(2)
  })
})
