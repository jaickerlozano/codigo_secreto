import { render, screen } from '@testing-library/react'
import { useQueryClient } from '@tanstack/react-query'
import { createMemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Providers } from './providers'
import { routes } from './router'

function QueryClientChecker() {
  const queryClient = useQueryClient()
  return <div data-testid="has-client">{queryClient ? 'yes' : 'no'}</div>
}

function Boom(): never {
  throw new Error('Expected render error')
}

describe('Providers', () => {
  it('renders children and provides a QueryClient', () => {
    const router = createMemoryRouter(routes)
    render(
      <Providers router={router}>
        <QueryClientChecker />
      </Providers>,
    )

    expect(screen.getByTestId('has-client').textContent).toBe('yes')
  })

  it('catches render errors and shows ErrorFallback', () => {
    const router = createMemoryRouter(routes)
    render(
      <Providers router={router}>
        <Boom />
      </Providers>,
    )

    expect(screen.getByRole('alert')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDefined()
  })
})
