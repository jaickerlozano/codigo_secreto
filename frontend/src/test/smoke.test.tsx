import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { routes } from '@/app/router.tsx'
import { queryClient } from '@/lib/query-client'

function renderWithProviders(ui: React.ReactNode) {
  return render(
    <QueryClientProvider client={queryClient()}>{ui}</QueryClientProvider>,
  )
}

describe('Smoke test', () => {
  it('renders the catalog through the router', async () => {
    window.localStorage.setItem('cs-age-verified', 'true')

    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(
      await screen.findByRole('heading', { name: 'Categorías destacadas' }, { timeout: 2000 }),
    ).toBeDefined()
    expect(screen.getByText('Los más vendidos')).toBeDefined()
  })
})
