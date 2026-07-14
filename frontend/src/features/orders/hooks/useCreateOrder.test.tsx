import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useCreateOrder } from './useCreateOrder'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

const guestPayload = {
  phone: '+56 9 1234 5678',
  shipping_address: 'Av. Providencia 1234',
  apartment_office: 'Depto 502',
  payment_method: 'webpay' as const,
  comuna_name: 'Providencia',
  region_name: 'Región Metropolitana',
  guest_email: 'test@example.com',
  guest_name: 'Valentina Gómez',
  guest_items: [{ product_id: 1, quantity: 1 }],
}

describe('useCreateOrder', () => {
  it('creates an order and returns the backend order_number', async () => {
    const { result } = renderHook(() => useCreateOrder(), { wrapper: Wrapper })

    act(() => {
      result.current.mutate(guestPayload)
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.order_number).toBeDefined()
    expect(result.current.data?.order_number).toMatch(/^CS-\d{6}$/)
  })
})
