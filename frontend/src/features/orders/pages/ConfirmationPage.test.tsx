import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it } from 'vitest'

import { useCartStore } from '@/features/cart'
import type { Product } from '@/features/catalog/types'
import type { components } from '@/api/schema.d.ts'
import { queryClient } from '@/lib/query-client'
import { testOrder } from '@/test/handlers/orders'
import { server } from '@/test/setup'
import { PendingPaymentPage } from '@/features/checkout/pages/PendingPaymentPage'
import { ConfirmationPage } from './ConfirmationPage'

type Order = components['schemas']['Order']
const product = { id: 1, name: 'Vibrador de prueba', price: 29990, category: '1', experienceLevel: 'intermedio', features: [], description: 'Descripción de prueba', materials: [], usageInstructions: '', icon: '✦', gradient: 'from-violet-950 via-purple-900 to-violet-800', sku: '101', stock: 10, image: null, images: [] } as Product
const routes = [{ path: '/confirmation/:orderNumber', element: <ConfirmationPage /> }, { path: '/checkout/payment/:orderNumber', element: <PendingPaymentPage /> }]
const orderUrl = 'http://localhost:8000/api/orders/by-order-number/CS-123456/'

function Wrapper({ children }: { children: ReactNode }) { return <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider> }

describe('ConfirmationPage', () => {
  beforeEach(() => { useCartStore.setState({ mode: 'guest', items: [{ product, quantity: 1 }] }) })

  it.each([
    { status: 'PAID' as Order['status'], heading: '¡Pedido confirmado!', clears: true, hidden: [] as string[] },
    { status: 'CANCELLED' as Order['status'], heading: 'Pedido cancelado', clears: false, hidden: ['Embalaje', 'Rastrear mi pedido'] },
    { status: 'PENDING' as Order['status'], heading: 'Pago pendiente', clears: false, hidden: ['¡Pedido confirmado!'] },
  ])('renders "$heading" only for the fetched $status order', async ({ status, heading, clears, hidden }) => {
    server.use(http.get(orderUrl, () => HttpResponse.json(status === 'PENDING' ? testOrder : { ...testOrder, status })))
    const router = createMemoryRouter(routes, { initialEntries: ['/confirmation/CS-123456'] })
    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByRole('heading', { name: heading })).toBeDefined()
    hidden.forEach((text) => expect(screen.queryByText(text)).toBeNull())
    if (status !== 'PENDING') expect(screen.getByText('Vibrador de prueba')).toBeDefined()
    if (clears) await waitFor(() => expect(useCartStore.getState().items).toHaveLength(0))
    else expect(useCartStore.getState().items).toHaveLength(1)
  })
})
