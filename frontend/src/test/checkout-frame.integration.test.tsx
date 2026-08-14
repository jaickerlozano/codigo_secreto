import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { routes } from '@/app/router.tsx'
import { useCartStore } from '@/features/cart'
import type { Product } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

const product = { id: 1, name: 'Vibrador de prueba', price: 29990, category: '1', experienceLevel: 'intermedio', features: [], description: 'Descripción de prueba', materials: [], usageInstructions: '', icon: '✦', gradient: 'from-violet-950 via-purple-900 to-violet-800', sku: '101', stock: 10, image: null, images: [] } as Product
const quote = { items: [{ product_id: 1, product_name: 'Vibrador de prueba', quantity: 1, unit_price: 29990, line_total: 29990 }], subtotal: 29990, shipping_cost: 3500, total: 33490, revision: 'gq1.frame' }

function renderApp(initialPath: string) {
  window.localStorage.setItem('cs-age-verified', 'true')
  server.use(
    // Keep the session unauthenticated so the cart stays in guest mode.
    http.get('http://localhost:8000/api/auth/me/', () => HttpResponse.json({ detail: 'no session' }, { status: 401 })),
    http.post('http://localhost:8000/api/orders/quote/', () => HttpResponse.json(quote)),
  )
  render(<QueryClientProvider client={queryClient()}><AuthProvider><RouterProvider router={createMemoryRouter(routes, { initialEntries: [initialPath] })} /></AuthProvider></QueryClientProvider>)
}

describe('checkout frame runtime harness', () => {
  it('deep-link/refresh with a persisted guest cart restarts safely at Data', async () => {
    useCartStore.setState({ mode: 'guest', items: [{ product, quantity: 1 }] })
    renderApp('/checkout')

    expect(await screen.findByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(screen.getByText('Datos')).toBeDefined()
    expect(screen.getByText('1', { selector: '[aria-current="step"]' })).toBeDefined()
    expect(screen.queryByRole('group', { name: 'Método de envío' })).toBeNull()
  })

  it('empty cart deep-link fails closed to the safe route', async () => {
    useCartStore.setState({ mode: 'guest', items: [] })
    renderApp('/checkout')

    expect(await screen.findByRole('heading', { name: 'Categorías destacadas' }, { timeout: 3000 })).toBeDefined()
  })

  it('CartDrawer CTA navigates to /checkout, closes the drawer, and lands on Data', async () => {
    useCartStore.setState({ mode: 'guest', items: [{ product, quantity: 1 }], isOpen: true })
    const user = userEvent.setup()
    renderApp('/')

    await user.click(await screen.findByRole('button', { name: /Continuar al pago/ }))

    expect(await screen.findByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(useCartStore.getState().isOpen).toBe(false)
    expect(screen.getByText('1', { selector: '[aria-current="step"]' })).toBeDefined()
  })
})
