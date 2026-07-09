import createClient from 'openapi-fetch'
import { toast } from 'sonner'

import type { Middleware } from 'openapi-fetch'
import type { paths } from '@/api/schema.d.ts'

import { csrfMiddleware } from './csrf'
import { env } from './env'

const client = createClient<paths>({
  baseUrl: env.API_URL,
  credentials: 'include',
})

export const errorMiddleware: Middleware = {
  async onResponse({ response }) {
    if (response.status === 401) {
      const next = encodeURIComponent(
        `${window.location.pathname}${window.location.search}`,
      )
      toast.error(
        'Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
      )
      window.location.assign(`/login?next=${next}`)
      return
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
