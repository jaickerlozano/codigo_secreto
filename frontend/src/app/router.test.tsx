import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { routes } from './router'

describe('router', () => {
  it('renders the home placeholder at /', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    render(<RouterProvider router={router} />)

    expect(screen.getByRole('heading', { name: 'Código Secreto' })).toBeDefined()
    expect(screen.getByText('Bienvenido a la tienda.')).toBeDefined()
  })

  it('renders the login placeholder at /login', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/login'] })
    render(<RouterProvider router={router} />)

    expect(screen.getByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(screen.getByText('Formulario de login próximamente.')).toBeDefined()
  })
})
