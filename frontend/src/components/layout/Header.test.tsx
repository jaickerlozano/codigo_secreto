import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { CATEGORIES } from '@/features/catalog/data/categories'

import { Header } from './Header'

const TEST_CATEGORIES = CATEGORIES.slice(0, 3)

describe('Header', () => {
  it('renders brand logo and navigation controls', () => {
    render(
      <MemoryRouter>
        <Header wishlistCount={1} categories={TEST_CATEGORIES} />
      </MemoryRouter>,
    )

    expect(screen.getByRole('button', { name: /Código Secreto — Inicio/i })).toBeDefined()
    expect(screen.getByRole('searchbox', { name: 'Buscar productos' })).toBeDefined()
    expect(screen.getByRole('button', { name: /Carrito — 0 productos/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /Favoritos — 1/i })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Abrir menú' })).toBeDefined()
  })

  it('renders category strip on desktop', () => {
    render(
      <MemoryRouter>
        <Header categories={TEST_CATEGORIES} />
      </MemoryRouter>,
    )

    for (const category of TEST_CATEGORIES) {
      expect(screen.getByText(category.name)).toBeDefined()
    }
  })
})
