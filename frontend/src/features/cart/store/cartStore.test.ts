import { describe, expect, it } from 'vitest'

import { useCartStore } from './cartStore'

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

describe('cartStore', () => {
  it('starts in guest mode', () => {
    expect(useCartStore.getState().mode).toBe('guest')
  })

  it('adds items in guest mode', () => {
    useCartStore.getState().addItem(testProduct)

    expect(useCartStore.getState().items).toHaveLength(1)
    expect(useCartStore.getState().items[0].quantity).toBe(1)
  })

  it('switches mode with setMode', () => {
    useCartStore.getState().setMode('authenticated')

    expect(useCartStore.getState().mode).toBe('authenticated')
  })

  it('accumulates quantity for the same product', () => {
    useCartStore.getState().addItem(testProduct)
    useCartStore.getState().addItem(testProduct)

    expect(useCartStore.getState().items[0].quantity).toBe(2)
  })

  it('removes an item by product id', () => {
    useCartStore.getState().addItem(testProduct)
    useCartStore.getState().removeItem(testProduct.id)

    expect(useCartStore.getState().items).toHaveLength(0)
  })
})
