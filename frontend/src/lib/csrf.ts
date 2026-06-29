import type { Middleware } from 'openapi-fetch'

export const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export function getCsrfToken(): string | undefined {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : undefined
}

export const csrfMiddleware: Middleware = {
  async onRequest({ request }) {
    if (UNSAFE_METHODS.has(request.method.toUpperCase())) {
      const token = getCsrfToken()
      if (token) {
        request.headers.set('X-CSRFToken', token)
      }
    }
    return request
  },
}
