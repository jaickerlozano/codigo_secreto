import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { routes } from '@/app/router.tsx'

describe('Smoke test', () => {
  it('renders the catalog through the router', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    render(<RouterProvider router={router} />)

    expect(
      screen.getByRole('heading', { name: 'Categorías destacadas' }),
    ).toBeDefined()
    expect(screen.getByText('Los más vendidos')).toBeDefined()
  })
})
