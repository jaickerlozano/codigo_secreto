import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PRODUCTS } from '../data/products'
import { ProductCard } from './ProductCard'

describe('ProductCard', () => {
  it('renders product name, price and add-to-cart button', () => {
    const product = PRODUCTS[0]

    render(
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
