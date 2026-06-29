import { render, screen } from '@testing-library/react'
import { useQueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'

import { Providers } from './providers'

function QueryClientChecker() {
  const queryClient = useQueryClient()
  return <div data-testid="has-client">{queryClient ? 'yes' : 'no'}</div>
}

describe('Providers', () => {
  it('renders children and provides a QueryClient', () => {
    render(
      <Providers>
        <QueryClientChecker />
      </Providers>,
    )

    expect(screen.getByTestId('has-client').textContent).toBe('yes')
  })
})
