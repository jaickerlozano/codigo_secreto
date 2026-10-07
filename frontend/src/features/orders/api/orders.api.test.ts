import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { server } from '@/test/setup'

import { createOrder, exchangeOrderAccessFromLocation, getOrderByNumber, getPendingOrder, cancelOrder } from './orders.api'
import { testOrder } from '@/test/handlers/orders'

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

describe('checkout recovery contract', () => {
  const payload = { phone: '+56', shipping_address: 'Address', guest_items: [] }
  it('seeds CSRF then prepares the cookie context before creation', async () => {
    const calls: string[] = []
    document.cookie = 'csrftoken=synthetic-csrf; path=/'
    server.use(
      http.get('http://localhost:8000/api/auth/csrf/', () => { calls.push('csrf'); return new HttpResponse(null, { status: 204 }) }),
      http.post('http://localhost:8000/api/orders/checkout-context/', ({ request }) => {
        calls.push('context')
        expect(request.credentials).toBe('include')
        expect(request.headers.get('X-CSRFToken')).toBe('synthetic-csrf')
        expect(request.headers.get('Idempotency-Key')).toBeNull()
        return new HttpResponse(null, { status: 204 })
      }),
      http.post('http://localhost:8000/api/orders/', () => { calls.push('create'); return HttpResponse.json(testOrder, { status: 201 }) }),
    )
    try {
      expect(await createOrder(payload)).toEqual(testOrder)
      expect(calls).toEqual(['csrf', 'context', 'create'])
    } finally { document.cookie = 'csrftoken=; max-age=0; path=/' }
  })
  it.each([403, 500])('never creates when context preparation fails (%s)', async status => {
    const create = vi.fn(() => HttpResponse.json(testOrder, { status: 201 }))
    server.use(
      http.post('http://localhost:8000/api/orders/checkout-context/', () => new HttpResponse(null, { status })),
      http.post('http://localhost:8000/api/orders/', create),
    )
    await expect(createOrder(payload)).rejects.toThrow()
    expect(create).not.toHaveBeenCalled()
  })
  it('does not prepare or create when the CSRF seed request fails', async () => {
    const context = vi.fn()
    const create = vi.fn()
    server.use(
      http.get('http://localhost:8000/api/auth/csrf/', () => new HttpResponse(null, { status: 500 })),
      http.post('http://localhost:8000/api/orders/checkout-context/', context),
      http.post('http://localhost:8000/api/orders/', create),
    )
    await expect(createOrder(payload)).rejects.toThrow()
    expect(context).not.toHaveBeenCalled()
    expect(create).not.toHaveBeenCalled()
  })
  it('maps an empty 204 to null, not undefined query data', async () => {
    expect(await getPendingOrder()).toBeNull()
  })
  it('recovers the unchanged server record repeatedly without any order POST', async () => {
    const create = vi.fn()
    server.use(
      http.get('http://localhost:8000/api/orders/pending/', () => HttpResponse.json(testOrder)),
      http.post('http://localhost:8000/api/orders/', create),
    )
    expect(await getPendingOrder()).toEqual(testOrder)
    expect(await getPendingOrder()).toEqual(testOrder)
    expect(create).not.toHaveBeenCalled()
  })
  it('cancels through the cookie-protected endpoint and retains stale conflict status', async () => {
    server.use(http.post('http://localhost:8000/api/orders/by-order-number/:orderNumber/cancel/', ({ request }) => {
      expect(request.credentials).toBe('include')
      expect(request.headers.get('X-Order-Capability')).toBeNull()
      return HttpResponse.json({ detail: 'El pedido ya cambió.' }, { status: 409 })
    }))
    await expect(cancelOrder('CS-123456')).rejects.toMatchObject({ status: 409 })
  })
})

describe('guest quote drift response', () => {
  it('surfaces the refreshed generated quote without retrying creation', async () => {
    server.use(http.post('http://localhost:8000/api/orders/', () => HttpResponse.json({ code: 'quote_revision_stale', detail: 'stale', refreshed_quote: { items: [], subtotal: 1, shipping_cost: 2, total: 3, revision: 'gq1.new' } }, { status: 400 })))
    await expect(createOrder({ phone: '+56', shipping_address: 'Address', guest_items: [], confirmed_revision: 'gq1.old' })).rejects.toMatchObject({ status: 400, refreshedQuote: { revision: 'gq1.new' } })
  })
})
