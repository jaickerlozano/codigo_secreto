import { describe, expect, it } from 'vitest'

import type { components } from '@/api/schema.d.ts'

import { mapApiProduct } from './mappers'

const apiProduct = {
  id: 7,
  name: 'Producto con reserva',
  price: 29990,
  image: null,
  image_original: null,
  images: [],
  category: 2,
  stock: 9,
  available_stock: 3,
  experience_level: 2,
  supplier: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
} satisfies components['schemas']['Product']

describe('mapApiProduct availability', () => {
  it('maps the generated available_stock field without deriving it from stock', () => {
    const product = mapApiProduct(apiProduct)

    expect(product.stock).toBe(9)
    expect(product.availableStock).toBe(3)
  })
})
