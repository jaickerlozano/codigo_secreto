import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { Product } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useCartStore } from '../store'

import { CartDrawer } from './CartDrawer'

const product = { id: 1, name: 'Producto de prueba', description: 'Descripción', icon: '✦', gradient: 'from-violet-900 to-purple-700' } as Product

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('CartDrawer', () => {
  it('renders empty cart state when open', () => {
    useCartStore.setState({ isOpen: true })

    render(<CartDrawer />, { wrapper: Wrapper })

    expect(
      document.body.contains(screen.getByText('Tu carrito está vacío')),
    ).toBe(true)
  })

  it('announces quote failures and retries the quote', async () => {
    let attempts = 0
    server.use(http.post('http://localhost:8000/api/orders/quote/', () => attempts++ === 0 ? HttpResponse.json({ detail: 'No pudimos calcular el total.' }, { status: 400 }) : HttpResponse.json({ items: [], subtotal: 29990, shipping_cost: 0, total: 29990, revision: 'gq1.retry' })))
    useCartStore.setState({ isOpen: true, items: [{ product, quantity: 1 }] })

    render(<CartDrawer />, { wrapper: Wrapper })

    expect((await screen.findByRole('alert')).textContent).toContain(
      'No pudimos calcular el total.',
    )
    await userEvent.click(
      screen.getByRole('button', { name: 'Reintentar cotización' }),
    )
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
    expect(screen.getAllByText('$29.990')).toHaveLength(2)
    expect(attempts).toBe(2)
  })
})
