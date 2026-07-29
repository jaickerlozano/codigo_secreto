import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { useCartStore } from '@/features/cart'

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

  it('uses the authenticated cart when mode is authenticated', async () => {
    useCartStore.setState({ mode: 'authenticated' })

    const { result } = renderHook(() => useCart(), { wrapper: Wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.mode).toBe('authenticated')
    expect(result.current.items).toEqual([])
  })
})
