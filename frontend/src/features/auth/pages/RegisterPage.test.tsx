import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { RegisterPage } from './RegisterPage'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('RegisterPage', () => {
  it('renders the registration heading and form', () => {
    const router = createMemoryRouter(
      [{ path: '/register', element: <RegisterPage /> }],
      { initialEntries: ['/register'] },
    )

    render(<RouterProvider router={router} />, { wrapper: Wrapper })

    expect(screen.getByRole('heading', { name: 'Crear cuenta' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Crear cuenta' })).toBeDefined()
    expect(screen.getByRole('link', { name: 'Inicia sesión' })).toBeDefined()
  })
})
