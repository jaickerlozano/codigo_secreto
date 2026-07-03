import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { PRODUCTS } from '../data/products'
import { ProductCard } from './ProductCard'

function renderWithRouter(ui: React.ReactNode) {
  const router = createMemoryRouter(
    [{ path: '/', element: ui }],
    { initialEntries: ['/'] },
  )
  return render(<RouterProvider router={router} />)
}

describe('ProductCard', () => {
  it('renders product name, price and add-to-cart button', () => {
    const product = PRODUCTS[0]

    renderWithRouter(
      <ProductCard
        product={product}
        onAddToCart={vi.fn()}
        onQuickView={vi.fn()}
      />,
    )

    expect(
      document.body.contains(screen.getByText(product.name)),
    ).toBe(true)
    expect(
      document.body.contains(
        screen.getByRole('button', { name: /Agregar al carrito/i }),
      ),
    ).toBe(true)
  })
})
