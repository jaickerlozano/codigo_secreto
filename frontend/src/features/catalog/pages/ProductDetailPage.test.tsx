import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { useCart } from '@/features/cart'

import { useCategories } from '../hooks/useCategories'
import { useProduct } from '../hooks/useProduct'
import { useProducts } from '../hooks/useProducts'
import type { Product } from '../types'
import { ProductDetailPage } from './ProductDetailPage'

vi.mock('@/features/cart', () => ({ useCart: vi.fn() }))
vi.mock('../hooks/useCategories', () => ({ useCategories: vi.fn() }))
vi.mock('../hooks/useProduct', () => ({ useProduct: vi.fn() }))
vi.mock('../hooks/useProducts', () => ({ useProducts: vi.fn() }))

const product: Product = {
  id: 1,
  name: 'Producto sin disponibilidad',
  price: 29990,
  category: 'Bienestar',
  experienceLevel: 'principiante',
  features: [],
  description: 'Descripción educativa',
  materials: [],
  usageInstructions: '',
  icon: '✦',
  gradient: 'from-violet-950 to-purple-900',
  sku: 'CS-1',
  stock: 8,
  availableStock: 0,
  image: null,
  images: [],
}

describe('ProductDetailPage availability', () => {
  it('shows a clear unavailable state and disables add-to-cart', () => {
    vi.mocked(useProduct).mockReturnValue({
      data: product,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useProduct>)
    vi.mocked(useCategories).mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useCategories>)
    vi.mocked(useProducts).mockReturnValue({
      data: { results: [] },
    } as unknown as ReturnType<typeof useProducts>)
    vi.mocked(useCart).mockReturnValue({
      addItemWithQuantity: vi.fn(),
    } as unknown as ReturnType<typeof useCart>)

    render(
      <MemoryRouter initialEntries={['/product/1']}>
        <Routes>
          <Route path="/product/:productId" element={<ProductDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('status').textContent).toContain(
      'No disponible por el momento',
    )
    expect(
      screen.getByRole('button', { name: 'No disponible' }),
    ).toHaveProperty('disabled', true)
    expect(
      screen.queryByRole('button', { name: /Aumentar cantidad/ }),
    ).toBeNull()
  })
})
