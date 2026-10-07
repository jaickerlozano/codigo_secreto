import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { http, HttpResponse, delay } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'
import { testOrder } from '@/test/handlers/orders'
import { PendingOrderNotice } from './PendingOrderNotice'

function setup(path = '/') {
  return render(<QueryClientProvider client={queryClient()}><AuthProvider><MemoryRouter initialEntries={[path]}><PendingOrderNotice /></MemoryRouter></AuthProvider></QueryClientProvider>)
}

describe('pending recovery notice', () => {
  it.each([false, true])('offers discreet cookie recovery for authenticated=%s', async authenticated => {
    const create = vi.fn()
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () => authenticated ? HttpResponse.json({ id: 1 }) : new HttpResponse(null, { status: 401 })),
      http.get('http://localhost:8000/api/orders/pending/', () => HttpResponse.json(testOrder)),
      http.post('http://localhost:8000/api/orders/', create),
    )
    setup()
    const link = await screen.findByRole('link', { name: 'Continuar pago' })
    expect(link.getAttribute('href')).toBe(`/checkout/payment/${testOrder.order_number}`)
    expect(screen.queryByText(testOrder.guest_name!)).toBeNull()
    expect(screen.queryByText(testOrder.guest_email!)).toBeNull()
    expect(screen.queryByText(testOrder.shipping_address)).toBeNull()
    expect(screen.queryByText('Vibrador de prueba')).toBeNull()
    expect(create).not.toHaveBeenCalled()
  })
  it('announces loading and treats guest 204 as normal absence', async () => {
    server.use(http.get('http://localhost:8000/api/orders/pending/', async () => { await delay(40); return new HttpResponse(null, { status: 204 }) }))
    setup()
    expect(screen.getByRole('region', { name: 'Preparando consulta de pedidos' }).getAttribute('aria-busy')).toBe('true')
    expect(await screen.findByRole('status', { name: 'Buscando pedido pendiente' })).toBeDefined()
    await waitFor(() => expect(screen.queryByRole('status', { name: 'Buscando pedido pendiente' })).toBeNull())
    expect(screen.queryByRole('region')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })
  it('keeps shared auth errors visible with a polite announcement and retry', async () => {
    let failed = true
    server.use(http.get('http://localhost:8000/api/auth/me/', () => failed ? new HttpResponse(null, { status: 500 }) : new HttpResponse(null, { status: 401 })))
    setup()
    expect(await screen.findByText(/No pudimos verificar tu sesión para consultar pedidos/, {}, { timeout: 3000 })).toBeDefined()
    expect(screen.getByRole('region', { name: 'Recuperar pedido' }).getAttribute('aria-live')).toBe('polite')
    failed = false
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar consulta' }))
    await waitFor(() => expect(screen.queryByText(/No pudimos verificar tu sesión/)).toBeNull())
  })
  it('shows an inline error and retries discovery', async () => {
    let fail = true
    server.use(http.get('http://localhost:8000/api/orders/pending/', () => fail ? HttpResponse.json({ detail: 'No disponible' }, { status: 500 }) : HttpResponse.json(testOrder)))
    setup()
    expect(await screen.findByRole('alert')).toBeDefined()
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar consulta' }))
    expect(await screen.findByRole('link', { name: 'Continuar pago' })).toBeDefined()
  })
  it.each(['/checkout/payment/CS-123456', '/order/CS-123456'])('avoids a redundant banner on %s', async path => {
    server.use(http.get('http://localhost:8000/api/orders/pending/', () => HttpResponse.json(testOrder)))
    setup(path)
    await waitFor(() => {
      expect(screen.queryByRole('region', { name: 'Preparando consulta de pedidos' })).toBeNull()
      expect(screen.queryByRole('status', { name: 'Buscando pedido pendiente' })).toBeNull()
    })
    expect(screen.queryByRole('region', { name: 'Pedido pendiente' })).toBeNull()
  })
  it('never offers payment for a due hold', async () => {
    server.use(http.get('http://localhost:8000/api/orders/pending/', () => HttpResponse.json({ ...testOrder, payment_expires_at: '2000-01-01T00:00:00Z' })))
    setup()
    expect(await screen.findByText('Plazo de pago vencido')).toBeDefined()
    expect(screen.queryByRole('link', { name: 'Continuar pago' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Ver pedido' })).toBeDefined()
  })
})
