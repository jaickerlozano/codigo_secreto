import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

  it('uses the shared uncropped studio stage for AI cutouts', () => {
    const product = {
      ...mockProduct,
      image: 'https://cdn.example.test/cutout.webp',
      imageOriginal: 'https://cdn.example.test/original.webp',
      isOnSale: true,
    }

    renderWithRouter(
      <ProductCard
        product={product}
        onAddToCart={vi.fn()}
        onQuickView={vi.fn()}
      />,
    )

    const image = screen.getByRole('img', { name: product.name })
    expect(image.className).toContain('object-contain')
    expect(screen.getByTestId('product-card-media-stage').parentElement?.className).toContain(
      'aspect-square'
    )
    expect(screen.getByTestId('product-card-media-stage').getAttribute('style')).toContain(
      'background-color: rgb(25, 19, 41)'
    )
    expect(screen.getByText('Oferta')).toBeTruthy()
  })

  it('falls back to the uncropped original before showing an accessible placeholder', async () => {
    const product = {
      ...mockProduct,
      image: 'https://cdn.example.test/cutout.webp',
      imageOriginal: 'https://cdn.example.test/original.webp',
    }

    renderWithRouter(
      <ProductCard
        product={product}
        onAddToCart={vi.fn()}
        onQuickView={vi.fn()}
      />,
    )

    const stage = screen.getByTestId('product-card-media-stage')
    const studioCanvas = stage.getAttribute('style')

    fireEvent.error(screen.getByRole('img', { name: product.name }))
    await waitFor(() =>
      expect(screen.getByRole('img', { name: product.name }).getAttribute('src')).toBe(
        product.imageOriginal,
      ),
    )
    expect(screen.getByRole('img', { name: product.name }).className).toContain(
      'object-contain'
    )
    expect(stage.getAttribute('style')).toBe(studioCanvas)
    expect(stage.querySelector('img[aria-hidden="true"]')).toBeNull()

    fireEvent.error(screen.getByRole('img', { name: product.name }))
    await waitFor(() =>
      expect(screen.getByRole('img', { name: product.name }).tagName).toBe('DIV'),
    )
  })
})
