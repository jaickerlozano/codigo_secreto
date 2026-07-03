import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Header } from './Header'

describe('Header', () => {
  it('renders brand logo and navigation controls', () => {
    render(
      <MemoryRouter>
        <Header cartCount={2} wishlistCount={1} categories={['Vibradores', 'Bienestar']} />
      </MemoryRouter>,
    )

    expect(screen.getByRole('button', { name: /Código Secreto — Inicio/i })).toBeDefined()
    expect(screen.getByRole('searchbox', { name: 'Buscar productos' })).toBeDefined()
    expect(screen.getByRole('button', { name: /Carrito — 2 productos/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /Favoritos — 1/i })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Abrir menú' })).toBeDefined()
  })

  it('renders category strip on desktop', () => {
    render(
      <MemoryRouter>
        <Header categories={['Vibradores', 'Bienestar', 'Kits']} />
      </MemoryRouter>,
    )

    expect(screen.getByText('Vibradores')).toBeDefined()
    expect(screen.getByText('Bienestar')).toBeDefined()
    expect(screen.getByText('Kits')).toBeDefined()
  })
})
