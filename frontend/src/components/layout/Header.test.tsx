import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import type { Category } from '@/features/catalog/types'

import { Header } from './Header'

const TEST_CATEGORIES: Category[] = [
  { id: 1, name: 'Vibradores', icon: '✦', gradient: 'from-violet-900 to-purple-700' },
  { id: 2, name: 'Lubricantes', icon: '◇', gradient: 'from-amber-900 to-yellow-700' },
  { id: 3, name: 'Juegos', icon: '❋', gradient: 'from-lime-900 to-emerald-700' },
]

describe('Header', () => {
  it('renders logo, search, cart and category navigation', () => {
    render(
      <MemoryRouter>
        <Header wishlistCount={1} categories={TEST_CATEGORIES} />
      </MemoryRouter>,
    )

    expect(
      screen.getByRole('button', { name: /Código Secreto — Inicio/i }),
    ).toBeDefined()
    expect(
      screen.getAllByRole('link', { name: /Vibradores/i }).length,
    ).toBeGreaterThan(0)
    expect(
      screen.getByRole('button', { name: /Carrito — 0 productos/i }),
    ).toBeDefined()
  })

  it('renders mobile menu categories when menu is opened', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(
      <MemoryRouter>
        <Header categories={TEST_CATEGORIES} />
      </MemoryRouter>,
    )

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)

    for (const category of TEST_CATEGORIES) {
      expect(
        screen.getAllByRole('link', { name: category.name }).length,
      ).toBeGreaterThan(0)
    }
  })
})
