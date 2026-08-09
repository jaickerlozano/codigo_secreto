import type { Middleware } from 'openapi-fetch'

export const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
export const CSRF_COOKIE_NAME = 'csrftoken'
export const CSRF_HEADER_NAME = 'X-CSRFToken'

export function getCookieValue(
  cookieString: string,
  cookieName: string
): string | undefined {
  const escapedName = cookieName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = cookieString.match(
    new RegExp(`(?:^|;\\s*)${escapedName}=([^;]*)`)
  )
  if (!match) return undefined

  try {
    return decodeURIComponent(match[1])
  } catch {
    return match[1]
  }
}

export function getCsrfToken(): string | undefined {
  return getCookieValue(globalThis.document?.cookie ?? '', CSRF_COOKIE_NAME)
}

export const csrfMiddleware: Middleware = {
  async onRequest({ request }) {
    if (UNSAFE_METHODS.has(request.method.toUpperCase())) {
      const token = getCsrfToken()
      if (token) {
        request.headers.set(CSRF_HEADER_NAME, token)
      }
    }
    return request
  },
}
