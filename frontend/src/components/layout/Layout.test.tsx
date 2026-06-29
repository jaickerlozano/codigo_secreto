import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Layout } from './Layout'

describe('Layout', () => {
  it('renders the header brand and outlet children', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<div data-testid="outlet-child">Outlet content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'Código Secreto' })).toBeDefined()
    expect(screen.getByTestId('outlet-child').textContent).toBe('Outlet content')
  })
})
