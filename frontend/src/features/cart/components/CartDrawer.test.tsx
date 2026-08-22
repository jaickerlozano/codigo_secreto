import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import {
  createMemoryRouter,
  MemoryRouter,
  Outlet,
  Route,
  RouterProvider,
  Routes,
} from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { CategoryPage } from '@/features/catalog'
import type { Product } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useCartStore } from '../store'

import { CartDrawer } from './CartDrawer'

// jsdom provides no layout APIs: Radix Slider renders `calc(NaN% + 0px)`
// and throws a CSS parse error. The price-range Slider inside the real
// CategoryPage rendered by the navigation test is UI chrome irrelevant to
// the flow under test (same pattern as contact.integration.test.tsx), so it
// is stubbed here.
vi.mock('@/components/ui/slider', () => ({ Slider: () => <div /> }))

const product = { id: 1, name: 'Producto de prueba', description: 'Descripción', icon: '✦', gradient: 'from-violet-900 to-purple-700' } as Product

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('CartDrawer', () => {
  it('shows authenticated cart loading instead of an empty cart', () => {
    server.use(http.get('http://localhost:8000/api/cart/me/', async () => {
      await new Promise((resolve) => setTimeout(resolve, 100))
      return HttpResponse.json({ items: [] })
    }))
    useCartStore.setState({ isOpen: true, mode: 'authenticated' })

    render(<CartDrawer />, { wrapper: Wrapper })

    expect(screen.getByRole('status').className).toContain('text-base')
    expect(screen.queryByText('Tu carrito está vacío')).toBeNull()
  })

  it('shows authenticated cart errors and retries', async () => {
    let attempts = 0
    server.use(http.get('http://localhost:8000/api/cart/me/', () => ++attempts < 3 ? HttpResponse.json({ detail: 'Cart unavailable.' }, { status: 500 }) : HttpResponse.json({ items: [] })))
    useCartStore.setState({ isOpen: true, mode: 'authenticated' })

    render(<CartDrawer />, { wrapper: Wrapper })

    const alert = await screen.findByRole('alert', undefined, { timeout: 2500 })
    expect(alert.querySelector('p')?.className).toContain('text-base')
    expect(screen.getByRole('button', { name: 'Retry cart' }).className).toContain('min-h-12')
    await userEvent.click(screen.getByRole('button', { name: 'Retry cart' }))
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
    expect(screen.getByText('Tu carrito está vacío')).toBeDefined()
    expect(attempts).toBe(3)
  })

  it('provides 48px quantity controls', () => {
    useCartStore.setState({ isOpen: true, items: [{ product, quantity: 1 }] })

    render(<CartDrawer />, { wrapper: Wrapper })

    expect(screen.getByRole('button', { name: `Reducir ${product.name}` }).className).toContain('h-12 w-12')
    expect(screen.getByRole('button', { name: `Aumentar ${product.name}` }).className).toContain('h-12 w-12')
  })

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

  it('navigates to /checkout and closes the drawer from the CTA', async () => {
    useCartStore.setState({ isOpen: true, items: [{ product, quantity: 1 }] })

    render(
      <QueryClientProvider client={queryClient()}>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<CartDrawer />} />
            <Route path="/checkout" element={<div>Checkout destino</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await userEvent.click(
      screen.getByRole('button', { name: /Continuar al pago/ }),
    )

    expect(await screen.findByText('Checkout destino')).toBeDefined()
    expect(useCartStore.getState().isOpen).toBe(false)
  })

  // Mirrors the real Layout: the drawer stays mounted while the routed
  // outlet below it swaps pages, so focus-order regressions surface here.
  function DrawerShell() {
    return (
      <>
        <CartDrawer />
        <Outlet />
      </>
    )
  }

  function renderDrawerShell(catalog = <CategoryPage />) {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <DrawerShell />,
          children: [
            { index: true, element: <div>Inicio</div> },
            { path: 'category/:categoryId', element: catalog },
          ],
        },
      ],
      { initialEntries: ['/'] },
    )

    render(
      <QueryClientProvider client={queryClient()}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )

    return router
  }

  it('navigates to /category/todos from "Seguir comprando", keeps the cart and focuses the catalog heading', async () => {
    useCartStore.setState({ isOpen: true, items: [{ product, quantity: 2 }] })

    const router = renderDrawerShell()

    await userEvent.click(
      screen.getByRole('button', { name: 'Seguir comprando' }),
    )

    const heading = await screen.findByRole('heading', {
      name: 'Todos los productos',
    })
    expect(router.state.location.pathname).toBe('/category/todos')
    expect(document.activeElement).toBe(heading)
    expect(useCartStore.getState().isOpen).toBe(false)
    expect(useCartStore.getState().items).toEqual([
      { product, quantity: 2 },
    ])
  })

  it('preserves every cart item and quantity and keeps history navigation working', async () => {
    const secondProduct = {
      id: 2,
      name: 'Otro producto',
      description: 'Descripción',
      icon: '♥',
      gradient: 'from-cyan-900 to-teal-700',
    } as Product
    useCartStore.setState({
      isOpen: true,
      items: [
        { product, quantity: 2 },
        { product: secondProduct, quantity: 1 },
      ],
    })

    // This scenario only asserts arrival, cart preservation, close and
    // history behavior — nothing page-specific — so it uses a light stub
    // for the catalog route instead of mounting the full CategoryPage
    // (keeps the parallel-pool footprint of the harness minimal).
    const router = renderDrawerShell(<div>Catálogo destino</div>)

    await userEvent.click(
      screen.getByRole('button', { name: 'Seguir comprando' }),
    )
    await screen.findByText('Catálogo destino')

    expect(useCartStore.getState().items).toEqual([
      { product, quantity: 2 },
      { product: secondProduct, quantity: 1 },
    ])

    router.navigate(-1)
    await screen.findByText('Inicio')
    expect(router.state.location.pathname).toBe('/')
    expect(useCartStore.getState().isOpen).toBe(false)
  })

  it('supports keyboard activation of "Seguir comprando" and lands focus in the catalog', async () => {
    useCartStore.setState({ isOpen: true, items: [{ product, quantity: 1 }] })

    const router = renderDrawerShell()

    const button = screen.getByRole('button', { name: 'Seguir comprando' })
    button.focus()
    await userEvent.keyboard('{Enter}')

    const heading = await screen.findByRole('heading', {
      name: 'Todos los productos',
    })
    expect(router.state.location.pathname).toBe('/category/todos')
    expect(document.activeElement).toBe(heading)
    expect(useCartStore.getState().isOpen).toBe(false)
  })
})
