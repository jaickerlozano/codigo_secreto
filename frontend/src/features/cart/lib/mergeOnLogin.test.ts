import { QueryClient } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { useCartStore } from '@/features/cart'
import { getCart } from '@/features/cart/api/cart.api'

import { mergeOnLogin } from './mergeOnLogin'

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

describe('mergeOnLogin', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
  })

  afterEach(() => {
    queryClient.clear()
  })

  it('merges guest items into the authenticated cart', async () => {
    useCartStore.setState({
      items: [{ product: testProduct, quantity: 2, subtotal: 20000 }],
      mode: 'guest',
    })

    await mergeOnLogin(useCartStore.getState().items, queryClient)

    expect(useCartStore.getState().mode).toBe('authenticated')
    expect(useCartStore.getState().items).toHaveLength(0)

    const cart = await getCart()
    expect(cart.items).toHaveLength(1)
    expect(cart.items[0].quantity).toBe(2)
  })

  it('handles an empty guest cart', async () => {
    useCartStore.setState({ items: [], mode: 'guest' })

    await mergeOnLogin(useCartStore.getState().items, queryClient)

    expect(useCartStore.getState().mode).toBe('authenticated')
    const cart = await getCart()
    expect(cart.items).toHaveLength(0)
  })
})
