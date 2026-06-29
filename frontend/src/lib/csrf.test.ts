import type { MiddlewareCallbackParams } from 'openapi-fetch'
import { describe, expect, it, vi } from 'vitest'

import { csrfMiddleware, getCsrfToken, UNSAFE_METHODS } from './csrf'

function middlewareParams(request: Request): MiddlewareCallbackParams {
  return {
    request,
    schemaPath: '/test/',
    params: { path: {}, query: {} },
    id: 'test-request-id',
    options: { baseUrl: 'http://localhost:8000' },
  } as unknown as MiddlewareCallbackParams
}

describe('csrf', () => {
  describe('UNSAFE_METHODS', () => {
    it('contains state-changing HTTP methods', () => {
      expect(UNSAFE_METHODS).toEqual(new Set(['POST', 'PUT', 'PATCH', 'DELETE']))
    })
  })

  describe('getCsrfToken', () => {
    it('returns undefined when no csrftoken cookie exists', () => {
      vi.stubGlobal('document', { cookie: 'sessionid=abc123; other=value' })

      expect(getCsrfToken()).toBeUndefined()

      vi.unstubAllGlobals()
    })

    it('returns the decoded csrftoken cookie value', () => {
      vi.stubGlobal('document', { cookie: 'csrftoken=abc%40123; sessionid=xyz' })

      expect(getCsrfToken()).toBe('abc@123')

      vi.unstubAllGlobals()
    })

    it('finds csrftoken when it appears between other cookies', () => {
      vi.stubGlobal('document', { cookie: 'sessionid=xyz; csrftoken=tokenValue; path=/' })

      expect(getCsrfToken()).toBe('tokenValue')

      vi.unstubAllGlobals()
    })
  })

  describe('csrfMiddleware', () => {
    it('sets X-CSRFToken header on unsafe methods', async () => {
      vi.stubGlobal('document', { cookie: 'csrftoken=csrfValue' })
      const request = new Request('http://localhost/api/auth/login/', { method: 'POST' })

      const result = await csrfMiddleware.onRequest!(middlewareParams(request))

      expect((result as Request).headers.get('X-CSRFToken')).toBe('csrfValue')
      vi.unstubAllGlobals()
    })

    it('does not set X-CSRFToken header on safe methods', async () => {
      vi.stubGlobal('document', { cookie: 'csrftoken=csrfValue' })
      const request = new Request('http://localhost/api/products/', { method: 'GET' })

      const result = await csrfMiddleware.onRequest!(middlewareParams(request))

      expect((result as Request).headers.get('X-CSRFToken')).toBeNull()
      vi.unstubAllGlobals()
    })

    it('does not set header when no csrftoken cookie exists', async () => {
      vi.stubGlobal('document', { cookie: 'sessionid=abc' })
      const request = new Request('http://localhost/api/auth/login/', { method: 'POST' })

      const result = await csrfMiddleware.onRequest!(middlewareParams(request))

      expect((result as Request).headers.get('X-CSRFToken')).toBeNull()
      vi.unstubAllGlobals()
    })
  })
})
