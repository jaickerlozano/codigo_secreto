import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Layout } from './Layout'

describe('Layout', () => {
  it('renders the header, skip link, outlet children and footer', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<Layout cartCount={2} wishlistCount={1} />}>
            <Route index element={<div data-testid="outlet-child">Outlet content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('button', { name: /Código Secreto — Inicio/i })).toBeDefined()
    expect(screen.getByRole('link', { name: /Saltar al contenido/i })).toBeDefined()
    expect(screen.getByTestId('outlet-child').textContent).toBe('Outlet content')
    expect(screen.getByRole('contentinfo')).toBeDefined()
  })

  it('renders age gate on first visit', () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    )

    expect(screen.getByRole('dialog')).toBeDefined()
  })
})
