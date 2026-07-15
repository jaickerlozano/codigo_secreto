import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useInitiatePayment } from './useInitiatePayment'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useInitiatePayment', () => {
  it('initiates payment and returns the mock payment url', async () => {
    const { result } = renderHook(() => useInitiatePayment(), {
      wrapper: Wrapper,
    })

    act(() => {
      result.current.mutate({ order_id: 123 })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.payment_url).toContain('mock-checkout')
    expect(result.current.data?.gateway_reference).toContain('token_simulado')
  })
})
