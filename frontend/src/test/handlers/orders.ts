import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Order = components['schemas']['Order']
type CreateOrderInput = components['schemas']['Order']
type OrderItem = components['schemas']['OrderItem']

let nextOrderId = 100

const trackedOrders = new Map<string, Order>()

function makeOrder(
  body: Partial<Order>,
  items: OrderItem[] = [],
  orderNumber?: string,
): Order {
  return {
    id: nextOrderId++,
    order_number:
      orderNumber ??
      body.order_number ??
      `CS-${Math.floor(100000 + Math.random() * 900000)}`,
    phone: body.phone ?? '+56 9 1234 5678',
    shipping_address: body.shipping_address ?? 'Av. Providencia 1234',
    apartment_office: body.apartment_office ?? null,
    guest_email: body.guest_email ?? null,
    guest_name: body.guest_name ?? null,
    payment_method: body.payment_method ?? 'webpay',
    subtotal: 29990,
    shipping_cost: 3490,
    total: 33480,
    status: 'PENDING',
    created_at: new Date().toISOString(),
    carrier: 'Chilexpress',
    tracking_number: 'CHX-9988776655',
    comuna_display: 'Providencia (Región Metropolitana)',
    items,
  }
}

export const orderHandlers = [
  http.post('*api/orders/', async ({ request }) => {
    const body = (await request.json()) as CreateOrderInput
    const order = makeOrder(body, [
      {
        id: 1,
        product_id: 1,
        product_name: 'Vibrador Luna Pro',
        price: 29990,
        quantity: 1,
        subtotal: 29990,
      },
    ])
    trackedOrders.set(order.order_number, order)
    return HttpResponse.json(order, { status: 201 })
  }),

  http.get('*api/orders/track/', ({ request }) => {
    const url = new URL(request.url)
    const orderNumber = url.searchParams.get('order_number')

    if (!orderNumber) {
      return HttpResponse.json(
        { detail: 'Debes indicar el número de pedido.' },
        { status: 400 },
      )
    }

    const order = trackedOrders.get(orderNumber)
    if (order) {
      return HttpResponse.json(order)
    }

    // Fallback mock order for any order number used in tests or direct navigation.
    return HttpResponse.json(
      makeOrder(
        {
          phone: '+56 9 1234 5678',
          shipping_address: 'Av. Providencia 1234',
          apartment_office: 'Depto 502',
          payment_method: 'webpay',
        },
        [
          {
            id: 1,
            product_id: 1,
            product_name: 'Vibrador Luna Pro',
            price: 29990,
            quantity: 1,
            subtotal: 29990,
          },
        ],
        orderNumber,
      ),
    )
  }),
]
