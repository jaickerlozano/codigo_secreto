import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Product } from '../types'
import { ProductModal } from './ProductModal'

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

describe('ProductModal', () => {
  it('renders the dialog with product details', () => {
    render(
      <ProductModal
        product={mockProduct}
        isOpen={true}
        onClose={vi.fn()}
        onAddToCart={vi.fn()}
      />,
    )

    expect(
      document.querySelector('[role="dialog"]'),
    ).toBeTruthy()
    expect(
      screen.getByRole('button', { name: /Agregar al carrito/i }),
    ).toBeDefined()
  })
})
