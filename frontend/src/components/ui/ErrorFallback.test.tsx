import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ErrorFallback } from './ErrorFallback'

describe('ErrorFallback', () => {
  it('renders the error message and a retry button', () => {
    const error = new Error('Something went wrong')
    const reset = vi.fn()

    render(<ErrorFallback error={error} resetErrorBoundary={reset} />)

    expect(screen.getByRole('alert').textContent).toContain('Something went wrong')
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDefined()
  })

  it('calls resetErrorBoundary when retry is clicked', () => {
    const error = new Error('Something went wrong')
    const reset = vi.fn()

    render(<ErrorFallback error={error} resetErrorBoundary={reset} />)
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(reset).toHaveBeenCalledTimes(1)
  })
})
