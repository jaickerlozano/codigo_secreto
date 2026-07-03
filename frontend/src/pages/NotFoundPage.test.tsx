import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { NotFoundPage } from './NotFoundPage'

describe('NotFoundPage', () => {
  it('renders 404 heading and navigation links', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('404')).toBeDefined()
    expect(screen.getByText('Página no encontrada')).toBeDefined()
    expect(screen.getByRole('link', { name: /Volver al inicio/i })).toBeDefined()
    expect(screen.getByRole('link', { name: /Explorar productos/i })).toBeDefined()
  })
})
