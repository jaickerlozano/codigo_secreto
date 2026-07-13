import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'
import { AuthProvider } from '@/features/auth/context/AuthContext'

import { ProtectedRoute } from './ProtectedRoute'

function Wrapper({ children }: { children: ReactNode }) {
  const client = queryClient()
  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

describe('ProtectedRoute', () => {
  it('renders children when the user is authenticated', async () => {
    server.use(
      http.get('*api/auth/me/', () =>
        HttpResponse.json({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          rut: null,
          phone: null,
          is_admin: false,
        }),
      ),
    )

    const router = createMemoryRouter(
      [
        {
          path: '/checkout',
          element: (
            <ProtectedRoute>
              <div data-testid="checkout-content">Checkout</div>
            </ProtectedRoute>
          ),
        },
      ],
      { initialEntries: ['/checkout'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByTestId('checkout-content')).toBeDefined()
  })

  it('redirects to login when the user is not authenticated', async () => {
    server.use(
      http.get('*api/auth/me/', () =>
        HttpResponse.json({ detail: 'No autenticado' }, { status: 401 }),
      ),
    )

    const router = createMemoryRouter(
      [
        {
          path: '/checkout',
          element: (
            <ProtectedRoute>
              <div data-testid="checkout-content">Checkout</div>
            </ProtectedRoute>
          ),
        },
        {
          path: '/login',
          element: <div data-testid="login-page">Iniciar sesión</div>,
        },
      ],
      { initialEntries: ['/checkout'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeDefined()
    })
  })
})
