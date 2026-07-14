import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useAddToCart } from './useAddToCart'
import { useCartItems } from './useCartItems'
import { useUpdateCartItem } from './useUpdateCartItem'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useUpdateCartItem', () => {
  it('updates the quantity of an authenticated cart item', async () => {
    const { result: addMutation } = renderHook(() => useAddToCart(), {
      wrapper: Wrapper,
    })

    addMutation.current.mutate({ product_id: 1, quantity: 2 })
    await waitFor(() => expect(addMutation.current.isSuccess).toBe(true))

    const { result: updateMutation } = renderHook(() => useUpdateCartItem(), {
      wrapper: Wrapper,
    })

    updateMutation.current.mutate({
      productId: 1,
      quantity: 5,
      currentQuantity: 2,
    })
    await waitFor(() => expect(updateMutation.current.isSuccess).toBe(true))

    const { result: query } = renderHook(
      () => useCartItems({ enabled: true }),
      { wrapper: Wrapper },
    )

    await waitFor(() => expect(query.current.isSuccess).toBe(true))
    expect(query.current.data?.items[0].quantity).toBe(5)
  })
})
