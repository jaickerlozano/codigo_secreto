import { render, screen } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { routes } from './router'

function renderWithProviders(ui: React.ReactNode) {
  return render(<QueryClientProvider client={queryClient()}>{ui}</QueryClientProvider>)
}

describe('router', () => {
  it('renders the home placeholder at /', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(screen.getByRole('heading', { name: 'Código Secreto' })).toBeDefined()
    expect(screen.getByText('Bienvenido a la tienda.')).toBeDefined()
  })

  it('renders the login page at /login', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/login'] })
    renderWithProviders(<RouterProvider router={router} />)

    expect(screen.getByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeDefined()
  })
})
