import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { toast } from 'sonner'

import { apiClient, errorMiddleware } from './api-client'
import { queryClient } from './query-client'

function onUnauthorized(path: string) { return errorMiddleware.onResponse?.({ request: new Request(`http://localhost:8000${path}`), response: new Response(null, { status: 401 }) } as Parameters<NonNullable<typeof errorMiddleware.onResponse>>[0]) }

describe('apiClient', () => {
  it('is frozen to prevent accidental mutation', () => {
    expect(Object.isFrozen(apiClient)).toBe(true)
  })

  it('attaches the readable CSRF cookie to unsafe generated-client requests', async () => {
    vi.stubGlobal('document', { cookie: 'csrftoken=csrfValue' })
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(null, { status: 204 }))

    await apiClient.POST('/api/orders/by-order-number/{order_number}/access/', {
      params: {
        header: { 'X-Order-Capability': 'fragment-token' },
        path: { order_number: 'CS-123456' },
      },
    })

    const request = fetchSpy.mock.calls[0][0] as Request
    expect(request.headers.get('X-CSRFToken')).toBe('csrfValue')
    fetchSpy.mockRestore()
    vi.unstubAllGlobals()
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
      value: {
        ...originalLocation,
        pathname: '/checkout',
        search: '?page=2',
        assign,
      },
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

  it('shows a toast on 401 for non-auth paths without redirecting', async () => {
    await errorMiddleware.onResponse?.({
      request: new Request('http://localhost:8000/api/cart/'),
      response: new Response(null, { status: 401 }),
    } as unknown as Parameters<
      NonNullable<typeof errorMiddleware.onResponse>
    >[0])

    expect(toast.error).toHaveBeenCalledWith(
      'Tu sesión ha expirado. Por favor inicia sesión nuevamente.'
    )
    expect(assign).not.toHaveBeenCalled()
  })

  it('shows a toast on 403 without redirecting', async () => {
    await errorMiddleware.onResponse?.({
      response: new Response(null, { status: 403 }),
    } as unknown as Parameters<
      NonNullable<typeof errorMiddleware.onResponse>
    >[0])

    expect(toast.error).toHaveBeenCalledWith(
      'No tienes permisos para esta acción.'
    )
    expect(assign).not.toHaveBeenCalled()
  })

  it('throws on 500 so the error boundary can catch it', async () => {
    await expect(
      errorMiddleware.onResponse?.({
        response: new Response(null, { status: 500 }),
      } as unknown as Parameters<
        NonNullable<typeof errorMiddleware.onResponse>
      >[0])
    ).rejects.toThrow('Error del servidor. Intenta más tarde.')
  })

  it('does nothing on successful responses', async () => {
    await errorMiddleware.onResponse?.({
      response: new Response(null, { status: 200 }),
    } as unknown as Parameters<
      NonNullable<typeof errorMiddleware.onResponse>
    >[0])

    expect(toast.error).not.toHaveBeenCalled()
    expect(assign).not.toHaveBeenCalled()
  })

  it('does not show toast or redirect on 401 for auth endpoints', async () => {
    const authPaths = [
      '/api/auth/login/',
      '/api/auth/register/',
      '/api/auth/me/',
      '/api/auth/logout/',
    ]

    for (const pathname of authPaths) {
      await errorMiddleware.onResponse?.({
        request: new Request(`http://localhost:8000${pathname}`),
        response: new Response(null, { status: 401 }),
      } as unknown as Parameters<
        NonNullable<typeof errorMiddleware.onResponse>
      >[0])
    }

    expect(toast.error).not.toHaveBeenCalled()
    expect(assign).not.toHaveBeenCalled()
  })

  it('shares one refresh request across concurrent 401 responses and retries once', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => { const request = input instanceof Request ? input : new Request(input); return new Response(null, { status: new URL(request.url).pathname === '/api/auth/token/refresh/' ? 204 : 200 }) })
    const results = await Promise.all(['/api/orders/', '/api/cart/me/'].map((path) => onUnauthorized(path)))

    expect(fetchSpy).toHaveBeenCalledTimes(3)
    expect(results.map((response) => response?.status)).toEqual([200, 200])
    fetchSpy.mockRestore()
  })

  it('clears the session and does not retry when refresh fails', async () => {
    const sessionExpired = vi.fn()
    window.addEventListener('auth:session-expired', sessionExpired)
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 401 }))

    const response = await onUnauthorized('/api/orders/')

    expect(response?.status).toBe(401)
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    expect(sessionExpired).toHaveBeenCalledTimes(1)
    for (const path of ['/api/auth/login/', '/api/auth/register/', '/api/auth/token/refresh/', '/api/auth/logout/', '/api/auth/csrf/', '/api/orders/by-order-number/CS-123456/access/']) await onUnauthorized(path)
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    window.removeEventListener('auth:session-expired', sessionExpired); fetchSpy.mockRestore()
  })
})
