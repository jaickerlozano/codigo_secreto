import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { ConfirmationPage } from './ConfirmationPage'

const ORDER_STORAGE_KEY = 'cs-last-order'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('ConfirmationPage', () => {
  beforeEach(() => {
    sessionStorage.setItem(ORDER_STORAGE_KEY, 'CS-123456')
  })

  afterEach(() => {
    sessionStorage.removeItem(ORDER_STORAGE_KEY)
  })

  it('renders order details and payment status', async () => {
    const router = createMemoryRouter(
      [{ path: '/confirmation', element: <ConfirmationPage /> }],
      { initialEntries: ['/confirmation'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(await screen.findByText('CS-123456')).toBeDefined()
    expect(screen.getByText('Pendiente de pago')).toBeDefined()
    expect(screen.getByText('Vibrador de prueba')).toBeDefined()
    expect(screen.getAllByText('$29.990').length).toBeGreaterThan(0)
    expect(screen.getByText('Av. Providencia 1234')).toBeDefined()
  })
})
