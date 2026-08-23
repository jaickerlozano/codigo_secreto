import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import type { Category } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { Header } from './Header'

const TEST_CATEGORIES: Category[] = [
  { id: 1, name: 'Vibradores', icon: '✦', gradient: 'from-violet-900 to-purple-700' },
  { id: 2, name: 'Lubricantes', icon: '◇', gradient: 'from-amber-900 to-yellow-700' },
  { id: 3, name: 'Juegos', icon: '❋', gradient: 'from-lime-900 to-emerald-700' },
]

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>
        <MemoryRouter>{children}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

describe('Header', () => {
  it('renders logo, search, cart, favorites link and category navigation', async () => {
    render(<Header categories={TEST_CATEGORIES} />, {
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
    expect((await screen.findByRole('link', { name: /Favoritos — 0/i })).getAttribute('href')).toBe('/favorites')
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

  it('shows Mis pedidos in desktop account dropdown when authenticated', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const accountButton = await screen.findByRole('button', { name: /Mi cuenta/i })
    await u.click(accountButton)
    expect(screen.getByRole('menuitem', { name: /Mis pedidos/i })).toBeDefined()
  })

  it('shows Mis pedidos in mobile menu when authenticated', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })
    await screen.findByRole('button', { name: /Mi cuenta/i })

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)
    expect(
      screen.getAllByRole('link', { name: /Mis pedidos/i }).length,
    ).toBeGreaterThan(0)
  })

  it('hides Mis pedidos from desktop dropdown and mobile menu for guests', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () =>
        new HttpResponse(null, { status: 401 }),
      ),
    )

    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const loginButton = await screen.findByRole('link', { name: /Iniciar sesión/i })
    expect(loginButton).toBeDefined()
    expect(screen.queryByRole('menuitem', { name: /Mis pedidos/i })).toBeNull()
    expect(screen.queryByRole('link', { name: /Mis pedidos/i })).toBeNull()

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)
    expect(screen.queryByRole('link', { name: /Mis pedidos/i })).toBeNull()
  })
})
