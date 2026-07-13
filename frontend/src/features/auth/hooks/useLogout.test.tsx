import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { queryClient } from '@/lib/query-client'

import { useLogout } from './useLogout'

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>
  )
}

describe('useLogout', () => {
  it('calls the logout endpoint and succeeds', async () => {
    const { result } = renderHook(() => useLogout(), { wrapper: Wrapper })

    result.current.mutate()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveProperty('message')
  })
})
