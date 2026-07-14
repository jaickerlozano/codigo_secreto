import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useAddToCart } from './useAddToCart'
import { useCartItems } from './useCartItems'
import { useRemoveFromCart } from './useRemoveFromCart'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useRemoveFromCart', () => {
  it('removes a product from the authenticated cart', async () => {
    const { result: addMutation } = renderHook(() => useAddToCart(), {
      wrapper: Wrapper,
    })

    addMutation.current.mutate({ product_id: 1, quantity: 2 })
    await waitFor(() => expect(addMutation.current.isSuccess).toBe(true))

    const { result: removeMutation } = renderHook(() => useRemoveFromCart(), {
      wrapper: Wrapper,
    })

    removeMutation.current.mutate({ product_id: 1, quantity: 2 })
    await waitFor(() => expect(removeMutation.current.isSuccess).toBe(true))

    const { result: query } = renderHook(
      () => useCartItems({ enabled: true }),
      { wrapper: Wrapper },
    )

    await waitFor(() => expect(query.current.isSuccess).toBe(true))
    expect(query.current.data?.items).toHaveLength(0)
  })
})
