import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { useCartStore } from '@/features/cart'
import { server } from '@/test/setup'

import { useCart } from './useCart'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

const testProduct = {
  id: 1,
  name: 'Producto de prueba',
  price: 10000,
  category: 'Vibradores',
  experienceLevel: 'principiante' as const,
  features: [],
  description: 'Descripción',
  materials: [],
  usageInstructions: '',
  icon: '✦',
  gradient: 'from-violet-900 to-purple-700',
  sku: '101',
  stock: 10,
  image: null,
  images: [],
}

describe('useCart', () => {
  it('uses the guest cart by default', () => {
    const { result } = renderHook(() => useCart(), { wrapper: Wrapper })

    expect(result.current.mode).toBe('guest')
    expect(result.current.items).toEqual([])
    expect(result.current.totalItems).toBe(0)
  })

  it('adds items to the guest cart', async () => {
    const { result } = renderHook(() => useCart(), { wrapper: Wrapper })

    act(() => {
      result.current.addItem(testProduct)
    })

    await waitFor(() => expect(result.current.items).toHaveLength(1))
    expect(result.current.totalItems).toBe(1)
  })

  it('uses backend quote totals for guest money fields', async () => {
    server.use(http.post('http://localhost:8000/api/orders/quote/', () => HttpResponse.json({ items: [], subtotal: 29990, revision: 'gq1.test' })))
    useCartStore.getState().addItem(testProduct)
    const { result } = renderHook(() => useCart(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.quoteIsLoading).toBe(false))
    expect(result.current.subtotal).toBe(29990)
    expect(result.current.total).toBeNull()
  })

  it('uses the authenticated cart when mode is authenticated', async () => {
    let quoteRequests = 0
    server.use(http.post('http://localhost:8000/api/orders/quote/', () => {
      quoteRequests += 1
      return HttpResponse.json({ items: [], subtotal: 29990, revision: 'gq1.unexpected' })
    }))
    useCartStore.setState({ mode: 'authenticated', items: [{ product: testProduct, quantity: 1 }] })

    const { result } = renderHook(() => useCart(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.mode).toBe('authenticated')
    expect(result.current.items).toEqual([])
    expect(quoteRequests).toBe(0)
  })

  it('requests a destination-priced authenticated cart and rekeys when comuna changes', async () => {
    const requestedComunas: string[] = []
    server.use(
      http.get('http://localhost:8000/api/cart/me/', ({ request }) => {
        const comuna = new URL(request.url).searchParams.get('comuna')
        requestedComunas.push(comuna ?? '')
        const shippingCost = comuna === '83' ? 4900 : 6200

        return HttpResponse.json({
          id: 1,
          created_at: '2026-07-09T00:00:00Z',
          updated_at: '2026-07-09T00:00:00Z',
          items: [],
          monto_total_final: 29990 + shippingCost,
          subtotal: 29990,
          shipping_cost: shippingCost,
          total: 29990 + shippingCost,
          free_shipping_progress: 0,
          free_shipping_threshold: 30000,
        })
      }),
    )
    useCartStore.setState({ mode: 'authenticated' })

    const { result, rerender } = renderHook(
      ({ comunaId }: { comunaId: number }) => useCart({ comunaId }),
      { initialProps: { comunaId: 83 }, wrapper: Wrapper },
    )

    await waitFor(() => expect(result.current.shippingCost).toBe(4900))
    expect(requestedComunas).toEqual(['83'])

    rerender({ comunaId: 84 })

    await waitFor(() => expect(result.current.shippingCost).toBe(6200))
    expect(requestedComunas).toEqual(['83', '84'])
  })
})
