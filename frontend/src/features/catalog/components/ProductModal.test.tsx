import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PRODUCTS } from '../data/products'
import { ProductModal } from './ProductModal'

describe('ProductModal', () => {
  it('renders the dialog with product details', () => {
    render(
      <ProductModal
        product={PRODUCTS[0]}
        isOpen={true}
        onClose={vi.fn()}
        onAddToCart={vi.fn()}
      />,
    )

    expect(
      document.querySelector('[role="dialog"]'),
    ).toBeTruthy()
    expect(
      document.body.contains(screen.getByText(PRODUCTS[0].name)),
    ).toBe(true)
  })
})
