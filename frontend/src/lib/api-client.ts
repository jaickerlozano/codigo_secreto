import createClient from 'openapi-fetch'
import { toast } from 'sonner'

import type { Middleware } from 'openapi-fetch'
import type { paths } from '@/api/schema.d.ts'

import { CSRF_HEADER_NAME, csrfMiddleware, getCsrfToken } from './csrf'
import { env } from './env'

const apiBaseUrl =
  import.meta.env.MODE === 'test'
    ? 'http://localhost:8000'
    : env.API_URL.startsWith('http://') || env.API_URL.startsWith('https://')
      ? env.API_URL
      : globalThis.location?.origin || 'http://localhost:8000'

const client = createClient<paths>({
  baseUrl: apiBaseUrl,
  credentials: 'include',
  fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
})

const AUTH_PATHS_SKIP_REFRESH = new Set([
  '/api/auth/login/',
  '/api/auth/register/',
  '/api/auth/token/refresh/',
  '/api/auth/me/',
  '/api/auth/logout/',
  '/api/auth/csrf/',
])

const REFRESH_PATH = '/api/auth/token/refresh/', SESSION_EXPIRED_EVENT = 'auth:session-expired', retryableRequests = new WeakMap<Request, Request>(); let refreshPromise: Promise<void> | null = null
function clearSession(): void { if (typeof window !== 'undefined') window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT)) }
function expiredResponse(response: Response): Response { clearSession(); toast.error('Tu sesión ha expirado. Por favor inicia sesión nuevamente.'); return response }
function refreshSession(): Promise<void> {
  if (!refreshPromise) {
    const csrfToken = getCsrfToken()
    refreshPromise = globalThis
      .fetch(new URL(REFRESH_PATH, apiBaseUrl), {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken ? { [CSRF_HEADER_NAME]: csrfToken } : undefined,
      })
      .then((response) => {
        if (!response.ok) throw new Error('La sesión no pudo renovarse.')
      })
      .finally(() => (refreshPromise = null))
  } return refreshPromise
}

export const errorMiddleware: Middleware = {
  async onRequest({ request }) { const retryRequest = request.clone(); retryRequest.headers.set('X-Session-Retry', '1'); retryableRequests.set(request, retryRequest); return request },
  async onResponse({ request, response }) {
    if (response.status === 401) {
      const pathname = new URL(request.url).pathname
      if (
        AUTH_PATHS_SKIP_REFRESH.has(pathname) ||
        pathname.endsWith('/access/')
      ) {
        return
      }

      try {
        await refreshSession()
        const retryRequest = retryableRequests.get(request) ?? request.clone()

        const retryResponse = await globalThis.fetch(retryRequest)
        if (retryResponse.status === 401) {
          return expiredResponse(retryResponse)
        }
        return retryResponse
      } catch {
        return expiredResponse(response)
      }
    }

    if (response.status === 403) {
      toast.error('No tienes permisos para esta acción.')
      return
    }

    if (response.status >= 500) {
      throw new Error('Error del servidor. Intenta más tarde.')
    }
  },
}

client.use(csrfMiddleware)
client.use(errorMiddleware)

export const apiClient = Object.freeze(client)
export { SESSION_EXPIRED_EVENT }
