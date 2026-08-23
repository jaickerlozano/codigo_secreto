import { render, screen, waitFor } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { isValidElement } from 'react'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { SESSION_EXPIRED_EVENT } from '@/lib/api-client'
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
  it('keeps guest checkout and confirmation routes public', () => {
    const types = ['checkout', 'confirmation'].map((path) => { const element = routes[0].children?.find((route) => route.path === path)?.element; return isValidElement(element) && typeof element.type === 'function' ? element.type.name : undefined })
    expect(types).toEqual(['CheckoutPage', 'ConfirmationPage'])
  })

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

  it('protects /orders and preserves the complete next destination including new', async () => {
    server.use(http.get('http://localhost:8000/api/auth/me/', () => HttpResponse.json({ detail: 'No autenticado' }, { status: 401 })))

    const router = createMemoryRouter(routes, { initialEntries: ['/orders?new=CS-1001'] })
    renderWithProviders(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login')
      expect(decodeURIComponent(router.state.location.search)).toContain('/orders?new=CS-1001')
    })
  })

  it('redirects to login on session expiry without leaking order content', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({ id: 1, email: 'buyer@example.com', first_name: 'Buyer', last_name: 'User', rut: null, phone: null, is_admin: false }),
      ),
    )

    const router = createMemoryRouter(routes, { initialEntries: ['/orders'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(await screen.findByText('Mis pedidos')).toBeDefined()

    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login')
      expect(decodeURIComponent(router.state.location.search)).toContain('next=/orders')
    })

    expect(screen.queryByText('CS-1001')).toBeNull()
  })
})
