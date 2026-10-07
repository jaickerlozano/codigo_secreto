import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { http, HttpResponse, delay } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'
import { testOrder } from '@/test/handlers/orders'
import type { Order } from '../api/orders.api'
import { useOrder } from '../hooks/useOrder'
import { PendingOrderActions } from './PendingOrderActions'

const cancelUrl = 'http://localhost:8000/api/orders/by-order-number/CS-123456/cancel/'
function setup(order = testOrder) {
  const client = queryClient()
  render(<QueryClientProvider client={client}><MemoryRouter><PendingOrderActions order={order} /></MemoryRouter></QueryClientProvider>)
  return { client, user: userEvent.setup() }
}

describe('explicit cancellation controls', () => {
  it('requires inline confirmation, labels its panel, and Escape returns focus', async () => {
    const cancel = vi.fn()
    server.use(http.post(cancelUrl, cancel))
    const { user } = setup()
    const trigger = screen.getByRole('button', { name: 'Cancelar pedido' })
    expect(trigger.getAttribute('aria-expanded')).toBe('false')
    await user.click(trigger)
    expect(trigger.getAttribute('aria-expanded')).toBe('true')
    const panel = screen.getByRole('group', { name: 'Confirmar cancelación' })
    expect(panel.id).toBe(trigger.getAttribute('aria-controls'))
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Sí, cancelar pedido' }))
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('group', { name: 'Confirmar cancelación' })).toBeNull()
    expect(document.activeElement).toBe(trigger)
    expect(cancel).not.toHaveBeenCalled()
  })
  it('cancels exactly once, announces pending/success, and never recreates an order', async () => {
    let calls = 0
    const create = vi.fn()
    server.use(
      http.post(cancelUrl, async () => { calls++; await delay(100); return HttpResponse.json({ ...testOrder, status: 'CANCELLED', cancellation_reason: 'BUYER' }) }),
      http.post('http://localhost:8000/api/orders/', create),
    )
    const { client, user } = setup()
    const keys = ['pending-order', 'order', 'orders', 'products', 'product', 'cart', 'guest-quote', 'dispatch-options']
    keys.forEach(key => client.setQueryData([key], 'cached'))
    await user.click(screen.getByRole('button', { name: 'Cancelar pedido' }))
    await user.dblClick(screen.getByRole('button', { name: 'Sí, cancelar pedido' }))
    expect(await screen.findByText('Cancelando pedido…')).toBeDefined()
    expect(await screen.findByText('Cancelado')).toBeDefined()
    expect(calls).toBe(1)
    expect(create).not.toHaveBeenCalled()
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Volver al catálogo' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Ver carrito' })).toBeDefined()
    await waitFor(() => keys.forEach(key => expect(client.getQueryState([key])?.isInvalidated).toBe(true)))
  })
  it('refreshes real status on a stale 409 and keeps the error visible', async () => {
    let order: Order = testOrder
    server.use(
      http.get('http://localhost:8000/api/orders/by-order-number/CS-123456/', () => HttpResponse.json(order)),
      http.post(cancelUrl, () => { order = { ...testOrder, status: 'PAID' }; return HttpResponse.json({ detail: 'Ya pagado' }, { status: 409 }) }),
    )
    function LiveOrder() {
      const query = useOrder('CS-123456')
      return query.data ? <><p>{query.data.status}</p><PendingOrderActions order={query.data} /></> : null
    }
    render(<QueryClientProvider client={queryClient()}><MemoryRouter><LiveOrder /></MemoryRouter></QueryClientProvider>)
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Cancelar pedido' }))
    await user.click(screen.getByRole('button', { name: 'Sí, cancelar pedido' }))
    expect(await screen.findByText('PAID')).toBeDefined()
    expect(screen.getByRole('alert').textContent).toContain('El estado del pedido cambió')
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cancelar pedido' })).toBeNull()
  })
  it.each([
    { status: 'PAID' as const },
    { status: 'CANCELLED' as const },
    { payment_expires_at: '2000-01-01T00:00:00Z' },
    { payment_expires_at: null },
    { payment_expires_at: 'invalid' },
  ])('never pays or cancels terminal/invalid holds: %j', overrides => {
    setup({ ...testOrder, ...overrides })
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cancelar pedido' })).toBeNull()
  })
  it('labels expiry differently from manual cancellation', () => {
    setup({ ...testOrder, status: 'CANCELLED', cancellation_reason: 'EXPIRED' })
    expect(screen.getByText('Vencido — plazo de pago vencido')).toBeDefined()
  })
  it('does not cancel on unmount', () => {
    const cancel = vi.fn()
    server.use(http.post(cancelUrl, cancel))
    const client = queryClient()
    const view = render(<QueryClientProvider client={client}><MemoryRouter><PendingOrderActions order={testOrder} /></MemoryRouter></QueryClientProvider>)
    view.unmount()
    expect(cancel).not.toHaveBeenCalled()
  })
})
