import { render, screen } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { routes } from './router'

function renderWithProviders(ui: React.ReactNode) {
  return render(
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>{ui}</AuthProvider>
    </QueryClientProvider>,
  )
}

describe('router', () => {
  it('renders the home catalog at /', async () => {
    window.localStorage.setItem('cs-age-verified', 'true')

    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(
      await screen.findByRole('heading', { name: 'Categorías destacadas' }),
    ).toBeDefined()
    expect(screen.getByText('Los más vendidos')).toBeDefined()
  })

  it('renders the login page at /login when not authenticated', async () => {
    server.use(
       http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({ detail: 'No autenticado' }, { status: 401 }),
      ),
    )

    const router = createMemoryRouter(routes, { initialEntries: ['/login'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(
      await screen.findByRole('heading', { name: 'Iniciar sesión' }),
    ).toBeDefined()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeDefined()
  })

  it('redirects to home at /login when already authenticated', async () => {
    window.localStorage.setItem('cs-age-verified', 'true')

    const router = createMemoryRouter(routes, { initialEntries: ['/login'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(
      await screen.findByRole('heading', { name: 'Categorías destacadas' }),
    ).toBeDefined()
  })
})
