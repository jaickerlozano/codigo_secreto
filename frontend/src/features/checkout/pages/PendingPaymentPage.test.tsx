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
const initiateUrl = 'http://localhost:8000/api/payments/initiate/'
const pending = (n: string, overrides: Partial<Order> = {}) => ({ ...testOrder, order_number: n, ...overrides })
const agreement409 = (overrides: Partial<Record<string, unknown>> = {}) => ({ code: 'special_delivery_agreement_required', detail: 'Coordina tu entrega especial por WhatsApp antes de pagar.', whatsapp_url: 'https://wa.me/56912345678?text=Hola', poll_after_seconds: 30, ...overrides })
function Wrapper({ children }: { children: ReactNode }) { return <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider> }
function setup(initialPath: string, state?: unknown) {
  const router = createMemoryRouter(routes, { initialEntries: [typeof state === 'undefined' ? initialPath : { pathname: initialPath, state }] })
  render(<RouterProvider router={router} />, { wrapper: Wrapper })
  return userEvent.setup()
}

describe('PendingPaymentPage', () => {
  beforeEach(() => { useCartStore.setState({ mode: 'guest', items: [{ product, quantity: 1 }] }) })
  afterEach(() => { vi.unstubAllEnvs(); vi.useRealTimers(); Object.defineProperty(navigator, 'onLine', { configurable: true, value: true }) })
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
  it('shows WhatsApp recovery guidance when special delivery blocks payment', async () => {
    server.use(
      http.get(orderUrl('CS-SPEC1'), () => HttpResponse.json(pending('CS-SPEC1', { delivery_kind: 'special', delivery_gate_status: 'blocked' }))),
      http.post(initiateUrl, () => HttpResponse.json(agreement409(), { status: 409 })),
    )
    const user = setup('/checkout/payment/CS-SPEC1')
    expect(await screen.findByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
    await user.click(screen.getByRole('button', { name: 'Continuar pago' }))
    const link = await screen.findByRole('link', { name: 'Coordinar por WhatsApp' })
    expect(link.getAttribute('href')).toBe('https://wa.me/56912345678?text=Hola')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toContain('noopener')
    expect(link.getAttribute('rel')).toContain('noreferrer')
    expect(screen.getByText(/coordina tu entrega especial por whatsapp antes de pagar/i)).toBeDefined()
    expect(screen.getByRole('button', { name: 'Revisar acuerdo' })).toBeDefined()
    expect(screen.queryByRole('button', { name: 'Continuar pago' })).toBeNull()
  })
  it('announces recovery and retries idempotently once the agreement is recorded', async () => {
    let gate: 'blocked' | 'ready' = 'blocked'
    let initiateCalls = 0
    const keys: (string | null)[] = []
    server.use(
      http.get(orderUrl('CS-SPEC2'), () => HttpResponse.json(pending('CS-SPEC2', { delivery_kind: 'special', delivery_gate_status: gate }))),
      http.post(initiateUrl, async ({ request }) => {
        initiateCalls += 1
        keys.push(request.headers.get('Idempotency-Key'))
        if (initiateCalls === 1) return HttpResponse.json(agreement409(), { status: 409 })
        return HttpResponse.json({ transaction_id: 9, order_id: 100, amount: 29990, payment_url: 'https://mock', gateway_reference: 'token' })
      }),
    )
    const user = setup('/checkout/payment/CS-SPEC2')
    await user.click(await screen.findByRole('button', { name: 'Continuar pago' }))
    expect(await screen.findByRole('link', { name: 'Coordinar por WhatsApp' })).toBeDefined()
    gate = 'ready'
    await user.click(screen.getByRole('button', { name: 'Revisar acuerdo' }))
    expect(await screen.findByText(/acuerdo registrado/i)).toBeDefined()
    expect(screen.getByRole('button', { name: 'Continuar pago' })).toBeDefined()
    await user.click(screen.getByRole('button', { name: 'Continuar pago' }))
    expect(await screen.findByRole('button', { name: 'Aprobar pago (simulado)' })).toBeDefined()
    expect(initiateCalls).toBe(2)
    expect(keys[0]).toBe(keys[1])
    expect(keys[0]).toBe('payment-100')
  })
  it('polls the gate while blocked and stops polling after recovery', async () => {
    let gate: 'blocked' | 'ready' = 'blocked'
    let orderGets = 0
    server.use(
      http.get(orderUrl('CS-POLL1'), () => { orderGets += 1; return HttpResponse.json(pending('CS-POLL1', { delivery_kind: 'special', delivery_gate_status: gate })) }),
      http.post(initiateUrl, () => HttpResponse.json(agreement409({ poll_after_seconds: 5 }), { status: 409 })),
    )
    const user = setup('/checkout/payment/CS-POLL1')
    await user.click(await screen.findByRole('button', { name: 'Continuar pago' }))
    expect(await screen.findByRole('link', { name: 'Coordinar por WhatsApp' })).toBeDefined()
    const getsBeforeRecovery = orderGets
    gate = 'ready'
    expect(await screen.findByText(/acuerdo registrado/i, undefined, { timeout: 7000 })).toBeDefined()
    expect(orderGets).toBeGreaterThan(getsBeforeRecovery)
    const getsAtRecovery = orderGets
    await new Promise((resolve) => setTimeout(resolve, 5600))
    expect(orderGets).toBe(getsAtRecovery)
  }, 15000)
  it('shows an offline notice and disables payment actions while offline', async () => {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })
    window.dispatchEvent(new Event('offline'))
    server.use(http.get(orderUrl('CS-OFF1'), () => HttpResponse.json(pending('CS-OFF1'))))
    setup('/checkout/payment/CS-OFF1')
    expect(await screen.findByRole('heading', { name: 'Pago pendiente' })).toBeDefined()
    expect(screen.getByText(/sin conexión a internet/i)).toBeDefined()
    const button = screen.getByRole('button', { name: 'Continuar pago' }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
    window.dispatchEvent(new Event('online'))
    await waitFor(() => {
      const onlineButton = screen.getByRole('button', { name: 'Continuar pago' }) as HTMLButtonElement
      expect(onlineButton.disabled).toBe(false)
    })
  })
})