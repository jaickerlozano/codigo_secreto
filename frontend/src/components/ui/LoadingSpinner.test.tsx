import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LoadingSpinner } from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders a loading indicator', () => {
    render(<LoadingSpinner />)

    expect(screen.getByRole('status').textContent).toContain('Cargando')
  })
})
