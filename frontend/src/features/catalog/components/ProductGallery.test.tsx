import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Product } from '../types'
import { ProductGallery } from './ProductGallery'

const product: Product = {
  id: 1,
  name: 'Luna Pro',
  price: 29990,
  category: 'Wellness',
  experienceLevel: 'principiante',
  features: [],
  description: 'Test product',
  materials: [],
  usageInstructions: '',
  icon: '✦',
  gradient: 'from-violet-950 to-purple-900',
  sku: 'CS-1',
  stock: 10,
  image: 'https://cdn.example.test/primary.webp',
  imageOriginal: 'https://cdn.example.test/primary-original.webp',
  images: [
    {
      id: 2,
      image: 'https://cdn.example.test/detail.webp',
      imageOriginal: 'https://cdn.example.test/detail-original.webp',
    },
  ],
}

describe('ProductGallery', () => {
  it('uses a stable media stage with a contained descriptive foreground image', () => {
    render(<ProductGallery product={product} />)

    const primaryImage = screen.getByRole('img', { name: 'Luna Pro' })
    expect(primaryImage.getAttribute('sizes')).toContain('42rem')
    expect(primaryImage.getAttribute('loading')).toBe('eager')
    expect(primaryImage.className).toContain('object-contain')
    expect(screen.getByTestId('product-gallery-stage').className).toContain(
      'aspect-[4/5]'
    )
    expect(screen.getByTestId('product-gallery-stage').className).toContain(
      'max-h-[calc(100dvh-8rem)]'
    )
    expect(screen.getByTestId('product-gallery-stage').className).toContain(
      'bg-base-900'
    )
  })

  it('uses the shared studio canvas for a successful AI cutout', () => {
    render(<ProductGallery product={product} />)

    const primaryImage = screen.getByRole('img', { name: 'Luna Pro' })
    const stage = primaryImage.parentElement
    expect(stage?.getAttribute('style')).toContain('background-color: rgb(25, 19, 41)')
    expect(stage?.getAttribute('style')).toContain('177, 74, 237')
    expect(stage?.getAttribute('style')).toContain('0, 102, 128')
    expect(stage?.getAttribute('style')).toContain('8, 5, 18')
    expect(primaryImage.getAttribute('src')).toBe(
      product.image
    )
  })

  it('uses the shared studio canvas when no AI cutout is available', () => {
    render(<ProductGallery product={{ ...product, imageOriginal: null }} />)

    expect(screen.getByRole('img', { name: 'Luna Pro' }).parentElement?.getAttribute('style')).toContain(
      'background-color: rgb(25, 19, 41)'
    )
  })

  it('uses the optimized original on the identical studio canvas when AI delivery fails', async () => {
    render(<ProductGallery product={product} />)

    const stage = screen.getByRole('img', { name: 'Luna Pro' }).parentElement
    const studioCanvas = stage?.getAttribute('style')

    fireEvent.error(screen.getByRole('img', { name: 'Luna Pro' }))

    await waitFor(() =>
      expect(screen.getByRole('img', { name: 'Luna Pro' }).getAttribute('src')).toBe(
        product.imageOriginal
      )
    )

    expect(stage?.getAttribute('style')).toBe(studioCanvas)
    expect(stage?.querySelector('img[aria-hidden="true"]')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'Ver imagen 2 de 2' }))

    await waitFor(() =>
      expect(screen.getByRole('img', { name: 'Luna Pro - Vista adicional' }).getAttribute('src')).toBe(
        product.images[0].image
      )
    )
    expect(
      screen.getByRole('img', { name: 'Luna Pro - Vista adicional' }).className
    ).toContain('object-contain')
  })

  it('keeps thumbnails as cropped square previews', () => {
    const { container } = render(<ProductGallery product={product} />)

    const thumbnails = container.querySelectorAll('button img[alt=""]')
    expect(thumbnails).toHaveLength(2)
    thumbnails.forEach((thumbnail) => {
      expect(thumbnail.className).toContain('object-cover')
    })
  })

  it('shows arrow controls and an image counter only for galleries with multiple images', () => {
    const { rerender } = render(<ProductGallery product={product} />)

    const previousButton = screen.getByRole('button', { name: 'Ver imagen anterior' })
    const nextButton = screen.getByRole('button', { name: 'Ver imagen siguiente' })
    expect(previousButton.className).toContain('h-12')
    expect(previousButton.className).toContain('w-12')
    expect(nextButton.className).toContain('h-12')
    expect(nextButton.className).toContain('w-12')
    expect(screen.getByText('1 / 2')).not.toBeNull()

    rerender(<ProductGallery product={{ ...product, images: [] }} />)

    expect(screen.queryByRole('button', { name: 'Ver imagen anterior' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Ver imagen siguiente' })).toBeNull()
    expect(screen.queryByText('1 / 1')).toBeNull()
  })

  it('navigates to the next image with the gallery arrow', async () => {
    render(<ProductGallery product={product} />)

    fireEvent.click(screen.getByRole('button', { name: 'Ver imagen siguiente' }))

    await waitFor(() => screen.getByRole('img', { name: 'Luna Pro - Vista adicional' }))
    expect(screen.getByText('2 / 2')).not.toBeNull()
  })

  it('wraps gallery arrows at the first and last images', async () => {
    render(<ProductGallery product={product} />)

    fireEvent.click(screen.getByRole('button', { name: 'Ver imagen anterior' }))

    await waitFor(() => screen.getByRole('img', { name: 'Luna Pro - Vista adicional' }))

    fireEvent.click(screen.getByRole('button', { name: 'Ver imagen siguiente' }))

    await waitFor(() => screen.getByRole('img', { name: 'Luna Pro' }))
    expect(screen.getByText('1 / 2')).not.toBeNull()
  })

  it('uses an accessible placeholder only when both AI and original delivery fail', async () => {
    render(<ProductGallery product={product} />)

    fireEvent.error(screen.getByRole('img', { name: 'Luna Pro' }))
    await waitFor(() =>
      expect(screen.getByRole('img', { name: 'Luna Pro' }).getAttribute('src')).toBe(
        product.imageOriginal
      )
    )
    fireEvent.error(screen.getByRole('img', { name: 'Luna Pro' }))

    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'Luna Pro' }).tagName).toBe('DIV')
      expect(screen.getAllByText('✦').length).toBeGreaterThan(0)
    })
  })
})
