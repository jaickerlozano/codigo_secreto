import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import type { Category } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'

import { Header } from './Header'

const TEST_CATEGORIES: Category[] = [
  { id: 1, name: 'Vibradores', icon: '✦', gradient: 'from-violet-900 to-purple-700' },
  { id: 2, name: 'Lubricantes', icon: '◇', gradient: 'from-amber-900 to-yellow-700' },
  { id: 3, name: 'Juegos', icon: '❋', gradient: 'from-lime-900 to-emerald-700' },
]

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Header', () => {
  it('renders logo, search, cart and category navigation', () => {
    render(<Header wishlistCount={1} categories={TEST_CATEGORIES} />, {
      wrapper: Wrapper,
    })

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

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)

    for (const category of TEST_CATEGORIES) {
      expect(
        screen.getAllByRole('link', { name: category.name }).length,
      ).toBeGreaterThan(0)
    }
  })
})
