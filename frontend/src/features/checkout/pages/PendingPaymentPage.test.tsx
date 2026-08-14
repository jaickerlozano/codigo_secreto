import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useCartStore } from '@/features/cart'
import type { Product } from '@/features/catalog/types'
import type { components } from '@/api/schema.d.ts'
import { queryClient } from '@/lib/query-client'
import { testOrder } from '@/test/handlers/orders'
import { server } from '@/test/setup'
import { ConfirmationPage } from '@/features/orders/pages/ConfirmationPage'
import { PendingPaymentPage } from './PendingPaymentPage'

type Order = components['schemas']['Order']
const product = { id: 1, name: 'Vibrador de prueba', price: 29990, category: '1', experienceLevel: 'intermedio', features: [], description: 'Descripción de prueba', materials: [], usageInstructions: '', icon: '✦', gradient: 'from-violet-950 via-purple-900 to-violet-800', sku: '101', stock: 10, image: null, images: [] } as Product
const routes = [{ path: '/', element: <p>Inicio</p> }, { path: '/checkout/payment/:orderNumber', element: <PendingPaymentPage /> }, { path: '/confirmation/:orderNumber', element: <ConfirmationPage /> }]
const orderUrl = (n: string) => `http://localhost:8000/api/orders/by-order-number/${n}/`
const pending = (n: string, overrides: Partial<Order> = {}) => ({ ...testOrder, order_number: n, ...overrides })
function Wrapper({ children }: { children: ReactNode }) { return <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider> }
function setup(initialPath: string, state?: unknown) {
  const router = createMemoryRouter(routes, { initialEntries: [typeof state === 'undefined' ? initialPath : { pathname: initialPath, state }] })
  render(<RouterProvider router={router} />, { wrapper: Wrapper })
  return userEvent.setup()
}

describe('PendingPaymentPage', () => {
  beforeEach(() => { useCartStore.setState({ mode: 'guest', items: [{ product, quantity: 1 }] }) })
  afterEach(() => { vi.unstubAllEnvs() })
  it('renders the truthful pending state from the fetched order', async () => {
    server.use(http.get(orderUrl('CS-PEND1'), () => HttpResponse.json(pending('CS-PEND1', { total: 33490 }))))
    setup('/checkout/payment/CS-PEND1', { transactionId: 7 })
    expect(await screen.findByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
    expect(screen.getByText('CS-PEND1')).toBeDefined()
    expect(screen.getByText('$33.490')).toBeDefined()
    expect(screen.getByText('Webpay')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Aprobar pago (simulado)' })).toBeDefined()
    expect(useCartStore.getState().items).toHaveLength(1)
  })
  it('approves exactly once and clears the guest cart only after the fetched PAID state', async () => {
    let order = pending('CS-APR1', { total: 33490 })
    server.use(http.get(orderUrl('CS-APR1'), () => HttpResponse.json(order)), http.post('http://localhost:8000/api/payments/7/mock-approve/', () => { order = { ...order, status: 'PAID' }; return HttpResponse.json({ transaction_id: 7, order_id: order.id, status: 'APPROVED', order_status: 'PAID' }) }))
    const user = setup('/checkout/payment/CS-APR1', { transactionId: 7 })
    await user.click(await screen.findByRole('button', { name: 'Aprobar pago (simulado)' }))
    expect(await screen.findByRole('heading', { name: '¡Pedido confirmado!' })).toBeDefined()
    await waitFor(() => expect(useCartStore.getState().items).toHaveLength(0))
  })
  it('keeps the pending order and cart when approval is rejected', async () => {
    server.use(http.get(orderUrl('CS-REJ1'), () => HttpResponse.json(pending('CS-REJ1'))), http.post('http://localhost:8000/api/payments/7/mock-approve/', () => HttpResponse.json({ transaction_id: ['Esta transacción no puede ser aprobada.'] }, { status: 400 })))
    const user = setup('/checkout/payment/CS-REJ1', { transactionId: 7 })
    await user.click(await screen.findByRole('button', { name: 'Aprobar pago (simulado)' }))
    expect((await screen.findByRole('alert')).textContent).toContain('Esta transacción no puede ser aprobada.')
    expect(screen.getByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
    expect(useCartStore.getState().items).toHaveLength(1)
  })
  it('denies the dev approval button outside development', async () => {
    vi.stubEnv('MODE', 'production')
    server.use(http.get(orderUrl('CS-PROD1'), () => HttpResponse.json(pending('CS-PROD1'))))
    setup('/checkout/payment/CS-PROD1')
    expect(await screen.findByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
    expect(screen.queryByRole('button', { name: 'Aprobar pago (simulado)' })).toBeNull()
    expect(screen.getByText(/no está disponible en este entorno/i)).toBeDefined()
    expect(useCartStore.getState().items).toHaveLength(1)
  })
  it('recovers the attempt on refresh by re-initiating before approving', async () => {
    server.use(http.get(orderUrl('CS-REF1'), () => HttpResponse.json(pending('CS-REF1'))))
    const user = setup('/checkout/payment/CS-REF1')
    await user.click(await screen.findByRole('button', { name: 'Continuar pago' }))
    expect(await screen.findByRole('button', { name: 'Aprobar pago (simulado)' })).toBeDefined()
  })
  it('offers retry when the order fetch fails', async () => {
    let failures = 2
    server.use(http.get(orderUrl('CS-ERR1'), () => { if (failures-- > 0) return HttpResponse.json({ detail: 'Not found.' }, { status: 404 }); return HttpResponse.json(pending('CS-ERR1')) }))
    const user = setup('/checkout/payment/CS-ERR1')
    expect(await screen.findByRole('alert', undefined, { timeout: 5000 })).toBeDefined()
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
  })
})
