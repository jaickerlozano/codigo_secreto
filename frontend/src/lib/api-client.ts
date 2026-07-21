import createClient from 'openapi-fetch'
import { toast } from 'sonner'

import type { Middleware } from 'openapi-fetch'
import type { paths } from '@/api/schema.d.ts'

import { csrfMiddleware } from './csrf'
import { env } from './env'

const client = createClient<paths>({
  baseUrl: '',
  credentials: 'include',
  // fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
})

const AUTH_PATHS_SKIP_401_REDIRECT = new Set([
  '/api/auth/login/',
  '/api/auth/register/',
  '/api/auth/me/',
  '/api/auth/logout/',
])

export const errorMiddleware: Middleware = {
  async onResponse({ request, response }) {
    if (response.status === 401) {
      const url = typeof request?.url === 'string' ? new URL(request.url) : null
      if (url && !AUTH_PATHS_SKIP_401_REDIRECT.has(url.pathname)) {
        toast.error(
          'Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
        )
      }
      return // Let the calling code handle the 401
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
