import type { ComponentProps, ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { http, HttpResponse } from 'msw'
import { afterEach, describe, expect, it, vi } from 'vitest'

const timelineMock = vi.hoisted(() => ({ shouldThrow: false }))

vi.mock('../components/OrderTimeline', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../components/OrderTimeline')>()

  return {
    ...actual,
    OrderTimeline: (props: ComponentProps<typeof actual.OrderTimeline>) => {
      if (timelineMock.shouldThrow) {
        throw new Error('Unable to render order timeline')
      }

      return <actual.OrderTimeline {...props} />
    },
  }
})

import { queryClient } from '@/lib/query-client'
import { AuthProvider } from '@/features/auth/context/AuthContext'
import { testOrder } from '@/test/handlers/orders'
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
  afterEach(() => {
    timelineMock.shouldThrow = false
  })

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
    expect(screen.getByRole('link', { name: 'Continuar pago' }).getAttribute('href')).toBe('/checkout/payment/CS-123456')
    expect(screen.getByRole('button', { name: 'Cancelar pedido' })).toBeDefined()
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

  it('invalidates recovery caches after successful guest email-ticket exchange', async () => {
    const client = queryClient()
    client.setQueryData(['pending-order', 0], null)
    client.setQueryData(['orders', 1], { results: [] })
    server.use(http.get('http://localhost:8000/api/auth/me/', () => new HttpResponse(null, { status: 401 })))
    const router = createMemoryRouter([{ path: '/order/:orderId', element: <OrderTrackingPage /> }], { initialEntries: ['/order/CS-123456#access=synthetic-ticket'] })
    render(<QueryClientProvider client={client}><AuthProvider><RouterProvider router={router} /></AuthProvider></QueryClientProvider>)
    expect(await screen.findByRole('link', { name: 'Continuar pago' })).toBeDefined()
    expect(client.getQueryState(['pending-order', 0])?.isInvalidated).toBe(true)
    expect(client.getQueryState(['orders', 1])?.isInvalidated).toBe(true)
  })

  it.each([401, 429])('does not offer actions when email-ticket exchange fails (%s)', async status => {
    server.use(http.post('http://localhost:8000/api/orders/by-order-number/CS-123456/access/', () => HttpResponse.json({ detail: 'Enlace no válido' }, { status })))
    const router = createMemoryRouter([{ path: '/order/:orderId', element: <OrderTrackingPage /> }], { initialEntries: ['/order/CS-123456#access=synthetic-ticket'] })
    render(<RouterProvider router={router} />, { wrapper: Wrapper })
    expect(await screen.findByRole('heading', { name: 'Pedido no encontrado' })).toBeDefined()
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cancelar pedido' })).toBeNull()
  })

  it('shows expiry reason without payment/cancellation actions', async () => {
    server.use(http.get('http://localhost:8000/api/orders/by-order-number/:orderNumber/', () => HttpResponse.json({ ...testOrder, status: 'CANCELLED', cancellation_reason: 'EXPIRED' })))
    const router = createMemoryRouter([{ path: '/order/:orderId', element: <OrderTrackingPage /> }], { initialEntries: ['/order/CS-123456'] })
    render(<RouterProvider router={router} />, { wrapper: Wrapper })
    expect(await screen.findByText('Vencido — plazo de pago vencido')).toBeDefined()
    expect(screen.getAllByText('Vencido').length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cancelar pedido' })).toBeNull()
  })

  it('shows the requested dispatch date without inventing an estimated delivery date', async () => {
    server.use(
      http.get('http://localhost:8000/api/orders/by-order-number/:orderNumber/', () =>
        HttpResponse.json({
          ...testOrder,
          requested_dispatch_date: '2026-09-01',
          estimated_delivery_date: null,
        }),
      ),
    )

    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByText('Fecha de despacho solicitada')).toBeDefined()
    expect(screen.getByText('1 de septiembre de 2026')).toBeDefined()
    expect(screen.queryByText('Entrega estimada')).toBeNull()
  })

  it('shows the estimated delivery date only when it is available', async () => {
    server.use(
      http.get('http://localhost:8000/api/orders/by-order-number/:orderNumber/', () =>
        HttpResponse.json({
          ...testOrder,
          requested_dispatch_date: null,
          estimated_delivery_date: '2026-09-03',
        }),
      ),
    )

    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByText('Entrega estimada')).toBeDefined()
    expect(screen.getByText('3 de septiembre de 2026')).toBeDefined()
    expect(screen.queryByText('Fecha de despacho solicitada')).toBeNull()
  })

  it('does not render logistics date details when neither date is available', async () => {
    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    await screen.findByText('CS-123456')

    expect(screen.queryByText('Fecha de despacho solicitada')).toBeNull()
    expect(screen.queryByText('Entrega estimada')).toBeNull()
  })
  it('shows an accessible retry fallback when the tracking route fails to render', async () => {
    timelineMock.shouldThrow = true
    const router = createMemoryRouter(
      [{ path: '/order/:orderId', element: <OrderTrackingPage /> }],
      { initialEntries: ['/order/CS-123456'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Unable to render order timeline',
    )
    timelineMock.shouldThrow = false
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('CS-123456')).toBeDefined()
  })
})
