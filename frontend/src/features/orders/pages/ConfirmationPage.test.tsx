import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { ConfirmationPage } from './ConfirmationPage'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('ConfirmationPage', () => {
  it('renders order details from in-memory navigation state', async () => {
    const router = createMemoryRouter(
      [{ path: '/confirmation', element: <ConfirmationPage /> }],
      {
        initialEntries: [
          { pathname: '/confirmation', state: { orderNumber: 'CS-123456' } },
        ],
      },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByText('CS-123456')).toBeDefined()
    expect(screen.getByText('Pendiente de pago')).toBeDefined()
    expect(screen.getByText('Vibrador de prueba')).toBeDefined()
    expect(screen.getAllByText('$29.990').length).toBeGreaterThan(2)
    expect(screen.getByText('Av. Providencia 1234')).toBeDefined()
  })

  it('redirects when confirmation has no in-memory order state', async () => {
    sessionStorage.setItem('cs-last-order', 'CS-legacy')
    const router = createMemoryRouter(
      [
        { path: '/', element: <p>Inicio</p> },
        { path: '/confirmation', element: <ConfirmationPage /> },
      ],
      { initialEntries: ['/confirmation'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByText('Inicio')).toBeDefined()
    expect(screen.queryByText('Número de pedido')).toBeNull()
  })
})
