import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useOrder } from './useOrder'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useOrder', () => {
  it('returns undefined when no order number is provided', () => {
    const { result } = renderHook(() => useOrder(undefined), {
      wrapper: Wrapper,
    })

    expect(result.current.isPending).toBe(true)
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('fetches an order by order_number', async () => {
    const { result } = renderHook(() => useOrder('CS-123456'), {
      wrapper: Wrapper,
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.order_number).toBe('CS-123456')
    expect(result.current.data?.subtotal).toBeDefined()
    expect(result.current.data?.total).toBeDefined()
    expect(result.current.data?.items).toBeDefined()
  })
})
