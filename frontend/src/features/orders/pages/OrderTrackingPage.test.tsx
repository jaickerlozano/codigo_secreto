import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { AuthProvider } from '@/features/auth/context/AuthContext'
import { server } from '@/test/setup'

import { OrderTrackingPage } from './OrderTrackingPage'

function Wrapper({ children }: { children: ReactNode }) {
  const client = queryClient()
  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

describe('OrderTrackingPage', () => {
  it('renders real order details for an authenticated user', async () => {
    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(
      screen.getByRole('status', { name: 'Cargando seguimiento del pedido' })
    ).toBeDefined()
    expect(await screen.findByText('CS-123456')).toBeDefined()
    expect(screen.getByText('Vibrador de prueba')).toBeDefined()
    expect(screen.getByText('Pendiente de pago')).toBeDefined()
    expect(screen.getByText('Av. Providencia 1234')).toBeDefined()
  })

  it('allows a guest to track an order through a capability fragment', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({ detail: 'No autenticado' }, { status: 401 })
      ),
      http.post(
        'http://localhost:8000/api/orders/by-order-number/CS-123456/access/',
        ({ request }) => {
          expect(request.headers.get('X-Order-Capability')).toBe('fragment-token')
          return new HttpResponse(null, { status: 204 })
        },
      )
    )

    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456#access=fragment-token'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.queryByText('No tienes permiso')).toBeNull()
    })

    expect(await screen.findByText('CS-123456')).toBeDefined()
    expect(screen.getByText('Vibrador de prueba')).toBeDefined()
  })
})
