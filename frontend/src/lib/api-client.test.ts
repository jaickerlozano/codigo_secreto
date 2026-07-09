import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { toast } from 'sonner'

import { apiClient, errorMiddleware } from './api-client'
import { queryClient } from './query-client'

describe('apiClient', () => {
  it('is frozen to prevent accidental mutation', () => {
    expect(Object.isFrozen(apiClient)).toBe(true)
  })
})

describe('queryClient', () => {
  it('returns a new QueryClient instance', () => {
    const client = queryClient()

    expect(client).toBeDefined()
    expect(client.getQueryCache()).toBeDefined()
  })
})

describe('errorMiddleware', () => {
  const assign = vi.fn()
  const originalLocation = window.location

  beforeEach(() => {
    assign.mockClear()
    vi.spyOn(toast, 'error').mockImplementation(() => 'toast-id')
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, pathname: '/checkout', search: '?page=2', assign },
      writable: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
      writable: true,
    })
  })

  it('redirects to login with next param on 401', async () => {
    await errorMiddleware.onResponse?.({
      response: new Response(null, { status: 401 }),
    } as unknown as Parameters<NonNullable<typeof errorMiddleware.onResponse>>[0])

    expect(toast.error).toHaveBeenCalledWith(
      'Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
    )
    expect(assign).toHaveBeenCalledWith('/login?next=%2Fcheckout%3Fpage%3D2')
  })

  it('shows a toast on 403 without redirecting', async () => {
    await errorMiddleware.onResponse?.({
      response: new Response(null, { status: 403 }),
    } as unknown as Parameters<NonNullable<typeof errorMiddleware.onResponse>>[0])

    expect(toast.error).toHaveBeenCalledWith('No tienes permisos para esta acción.')
    expect(assign).not.toHaveBeenCalled()
  })

  it('throws on 500 so the error boundary can catch it', async () => {
    await expect(
      errorMiddleware.onResponse?.({
        response: new Response(null, { status: 500 }),
      } as unknown as Parameters<NonNullable<typeof errorMiddleware.onResponse>>[0]),
    ).rejects.toThrow('Error del servidor. Intenta más tarde.')
  })

  it('does nothing on successful responses', async () => {
    await errorMiddleware.onResponse?.({
      response: new Response(null, { status: 200 }),
    } as unknown as Parameters<NonNullable<typeof errorMiddleware.onResponse>>[0])

    expect(toast.error).not.toHaveBeenCalled()
    expect(assign).not.toHaveBeenCalled()
  })
})
