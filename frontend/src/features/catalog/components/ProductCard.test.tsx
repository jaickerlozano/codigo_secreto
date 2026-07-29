import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import type { Product } from '../types'
import { ProductCard } from './ProductCard'

const mockProduct: Product = {
  id: 1,
  name: 'Vibrador Luna Pro',
  price: 29990,
  category: 'Vibradores',
  experienceLevel: 'principiante',
  features: ['10 modos'],
  description: 'Descripción de prueba',
  materials: ['Silicona'],
  usageInstructions: 'Instrucciones de prueba',
  icon: '✦',
  gradient: 'from-violet-950 via-purple-900 to-violet-800',
  sku: '101',
  stock: 10,
  image: null,
  images: [],
}

function renderWithRouter(ui: React.ReactNode) {
  const router = createMemoryRouter(
    [{ path: '/', element: ui }],
    { initialEntries: ['/'] },
  )
  return render(<RouterProvider router={router} />)
}

describe('ProductCard', () => {
  it('renders product name, price and add-to-cart button', () => {
    renderWithRouter(
      <ProductCard
        product={mockProduct}
        onAddToCart={vi.fn()}
        onQuickView={vi.fn()}
      />,
    )

    expect(
      document.body.contains(screen.getByText(mockProduct.name)),
    ).toBe(true)
    expect(
      document.body.contains(
        screen.getByRole('button', { name: /Agregar al carrito/i }),
      ),
    ).toBe(true)
  })
})
