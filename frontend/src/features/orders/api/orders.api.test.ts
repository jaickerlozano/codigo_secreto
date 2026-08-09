import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { server } from '@/test/setup'

import { exchangeOrderAccessFromLocation, getOrderByNumber } from './orders.api'

describe('order access routing', () => {
  const route = (hash = '', search = '') => ({
    hash,
    pathname: '/order/CS-123456',
    search,
  })

  it('exchanges a fragment proof without leaking it into URL or referrer', async () => {
    const token = 'secret-fragment-token'
    const replaceState = vi.fn()
    let exchangeRequest: Request | undefined

    server.use(
      http.post(
        'http://localhost:8000/api/orders/by-order-number/:orderNumber/access/',
        ({ request }) => {
          exchangeRequest = request
          return new HttpResponse(null, { status: 204 })
        }
      )
    )

    const exchanged = await exchangeOrderAccessFromLocation(
      'CS-123456',
      route(`#access=${encodeURIComponent(token)}`),
      { replaceState }
    )

    expect(exchanged).toBe(true)
    expect(exchangeRequest?.headers.get('X-Order-Capability')).toBe(token)
    expect(exchangeRequest?.url).not.toContain(token)
    expect(exchangeRequest?.referrer ?? '').not.toContain(token)
    expect(replaceState).toHaveBeenCalledWith(null, '', '/order/CS-123456')
  })

  it('does not exchange query or path proofs', async () => {
    const replaceState = vi.fn()
    const fetchSpy = vi.spyOn(globalThis, 'fetch')

    const exchanged = await exchangeOrderAccessFromLocation(
      'CS-123456',
      {
        ...route('', '?access=query-proof-token'),
        pathname: `${route().pathname}/path-proof-token`,
      },
      { replaceState }
    )

    expect(exchanged).toBe(false)
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(replaceState).not.toHaveBeenCalled()
  })

  it('reloads a clean route through the cookie-backed order lookup', async () => {
    let lookupRequest: Request | undefined

    server.use(
      http.get(
        'http://localhost:8000/api/orders/by-order-number/:orderNumber/',
        ({ request }) => {
          lookupRequest = request
          return HttpResponse.json({ order_number: 'CS-123456' })
        }
      )
    )

    await getOrderByNumber('CS-123456')

    expect(lookupRequest?.url).toBe(
      'http://localhost:8000/api/orders/by-order-number/CS-123456/'
    )
    expect(lookupRequest?.url).not.toContain('access=')
    expect(lookupRequest?.headers.get('X-Order-Capability')).toBeNull()
  })
})
