import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { render, renderHook, screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { AuthProvider, useAuth } from './AuthContext'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}

describe('AuthProvider', () => {
  it('throws when useAuth is called outside the provider', () => {
    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth debe usarse dentro de un AuthProvider',
    )
  })

  it('provides an unauthenticated state by default', async () => {
    server.use(
       http.get('http://localhost:8000/api/auth/me/', () =>
        HttpResponse.json({ detail: 'No autenticado' }, { status: 401 }),
      ),
    )

    function Consumer() {
      const { isAuthenticated, isLoading } = useAuth()
      return (
        <div>
          <span data-testid="auth-loading">{isLoading ? 'loading' : 'idle'}</span>
          <span data-testid="auth-status">
            {isAuthenticated ? 'authenticated' : 'guest'}
          </span>
        </div>
      )
    }

    render(
      <Wrapper>
        <Consumer />
      </Wrapper>,
    )

    await waitFor(() =>
      expect(screen.getByTestId('auth-loading').textContent).toBe('idle'),
    )
    expect(screen.getByTestId('auth-status').textContent).toBe('guest')
  })
})
