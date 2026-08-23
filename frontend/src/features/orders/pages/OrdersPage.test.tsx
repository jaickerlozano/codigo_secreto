import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { MemoryRouter, Routes, Route } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { OrdersPage } from './OrdersPage'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <MemoryRouter initialEntries={['/orders']}>
        <Routes><Route path="/orders" element={children} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const QpWrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
)

describe('OrdersPage', () => {
  it('shows a loading skeleton with status role', () => {
    render(<OrdersPage />, { wrapper: Wrapper })
    expect(screen.getByRole('status')).toBeDefined()
  })

  it('renders every order status unfiltered', async () => {
    render(<OrdersPage />, { wrapper: Wrapper })
    expect(await screen.findByText('Pagado / Listo para despacho')).toBeDefined()
    expect(screen.getByText('Enviado a destino')).toBeDefined()
    expect(screen.getByText('Pendiente de pago')).toBeDefined()
  })

  it('shows an accessible empty state for an empty list', async () => {
    server.use(http.get('http://localhost:8000/api/orders/', () => HttpResponse.json({ count: 0, next: null, previous: null, results: [] })))
    render(<OrdersPage />, { wrapper: Wrapper })
    expect(await screen.findByText('Aún no tienes pedidos')).toBeDefined()
  })

  it('shows a retryable error alert on failure', async () => {
    server.use(http.get('http://localhost:8000/api/orders/', () => HttpResponse.json({ detail: 'Error' }, { status: 500 })))
    render(<OrdersPage />, { wrapper: Wrapper })
    expect((await screen.findByRole('alert', {}, { timeout: 3000 })).textContent).toContain('No se pudieron cargar los pedidos')
  })

  it('highlights the matching new order with visible text, ring, and no scroll/focus', async () => {
    const scrollSpy = vi.spyOn(Element.prototype, 'scrollIntoView')
    render(
      <MemoryRouter initialEntries={['/orders?new=CS-1002']}>
        <Routes><Route path="/orders" element={<OrdersPage />} /></Routes>
      </MemoryRouter>,
      { wrapper: QpWrapper }
    )
    const badge = await screen.findByText('Pedido recién realizado')
    expect(badge.closest('article')?.getAttribute('data-highlighted')).toBe('true')
    expect(scrollSpy).not.toHaveBeenCalled()
    expect(document.activeElement).toBe(document.body)
  })

  it('does not highlight when the new parameter does not match', async () => {
    render(
      <MemoryRouter initialEntries={['/orders?new=CS-9999']}>
        <Routes><Route path="/orders" element={<OrdersPage />} /></Routes>
      </MemoryRouter>,
      { wrapper: QpWrapper }
    )
    await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
    expect(screen.queryByText('Pedido recién realizado')).toBeNull()
  })

  it('retries the request when the retry button is clicked', async () => {
    let calls = 0
    server.use(http.get('http://localhost:8000/api/orders/', () => {
      calls++
      if (calls <= 2) return HttpResponse.json({ detail: 'Error' }, { status: 500 })
      return HttpResponse.json({ count: 1, next: null, previous: null, results: [{ id: 1, order_number: 'CS-RETRY', status: 'PAID', total: 29990, created_at: '2026-07-14T10:30:00Z' }] })
    }))
    render(<OrdersPage />, { wrapper: Wrapper })
    fireEvent.click((await screen.findByRole('alert', {}, { timeout: 3000 })).querySelector('button') as HTMLElement)
    expect(await screen.findByText('CS-RETRY')).toBeDefined()
  })
})
