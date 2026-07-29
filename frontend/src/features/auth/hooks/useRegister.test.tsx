import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { useRegister } from './useRegister'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useRegister', () => {
  it('creates an account and returns the success message', async () => {
    const { result } = renderHook(() => useRegister(), { wrapper: Wrapper })

    result.current.mutate({
      first_name: 'María',
      last_name: 'González',
      email: 'maria@example.com',
      password: 'SecurePass123!',
      password_confirm: 'SecurePass123!',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveProperty('message')
  })

  it('exposes server errors on failure', async () => {
    server.use(
       http.post('http://localhost:8000/api/auth/register/', () =>
        HttpResponse.json({ detail: 'Email ya registrado' }, { status: 400 }),
      ),
    )

    const { result } = renderHook(() => useRegister(), { wrapper: Wrapper })

    result.current.mutate({
      first_name: 'María',
      last_name: 'González',
      email: 'duplicado@example.com',
      password: 'SecurePass123!',
      password_confirm: 'SecurePass123!',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toBeInstanceOf(Error)
  })
})
