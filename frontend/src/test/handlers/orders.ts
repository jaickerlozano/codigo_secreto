import { http, HttpResponse } from 'msw'

import type { components, paths } from '@/api/schema.d.ts'

type Order = components['schemas']['Order']
type CreateOrderInput = NonNullable<
  paths['/api/orders/']['post']['requestBody']
>['content']['application/json']
type OrderItem = components['schemas']['OrderItem']

let nextOrderId = 100

const trackedOrders = new Map<string, Order>()

function makeOrder(
  body: Partial<Order>,
  items: OrderItem[] = [],
  orderNumber?: string
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
    guest_access: body.guest_access ?? null,
    comuna: body.comuna,
    comuna_name: body.comuna_name ?? 'Providencia',
    comuna_display: `${body.comuna_name ?? 'Providencia'}, ${body.region_name ?? 'Región Metropolitana'}`,
    region_name: body.region_name ?? 'Región Metropolitana',
    payment_method: body.payment_method ?? 'webpay',
    subtotal: 29990,
    shipping_cost: 0,
    total: 29990,
    status: 'PENDING',
    created_at: new Date().toISOString(),
    carrier: 'Chilexpress',
    tracking_number: 'CHX-9988776655',
    delivery_kind: body.delivery_kind ?? 'standard',
    requested_dispatch_date: body.requested_dispatch_date ?? null,
    special_delivery_agreed_at: body.special_delivery_agreed_at ?? null,
    estimated_delivery_date: body.estimated_delivery_date ?? null,
    dispatched_at: body.dispatched_at ?? null,
    items,
  }
}

export const testOrder: Order = makeOrder(
  {
    order_number: 'CS-123456',
    phone: '+56 9 1234 5678',
    shipping_address: 'Av. Providencia 1234',
    apartment_office: 'Depto 502',
    guest_email: 'guest@example.com',
    guest_name: 'Valentina G.',
    comuna: 1,
    comuna_name: 'Providencia',
    region_name: 'Región Metropolitana',
    payment_method: 'webpay',
    shipping_cost: 0,
    total: 29990,
    status: 'PENDING',
    created_at: '2026-07-14T10:30:00Z',
  },
  [
    {
      id: 1,
      product_id: 1,
      product_name: 'Vibrador de prueba',
      price: 10000,
      quantity: 1,
      subtotal: 29990,
    },
  ]
)

export const orderHandlers = [
  http.post('http://localhost:8000/api/orders/', async ({ request }) => {
    const body = (await request.json()) as CreateOrderInput
    const order = makeOrder(body, [
      {
        id: 1,
        product_id: 1,
        product_name: 'Vibrador de prueba',
        price: 29990,
        quantity: 1,
        subtotal: 29990,
      },
    ])
    trackedOrders.set(order.order_number, order)
    return HttpResponse.json(order, { status: 201 })
  }),

  http.get(
    'http://localhost:8000/api/orders/by-order-number/:orderNumber/',
    ({ params }) => {
      const orderNumber = params.orderNumber as string
      return HttpResponse.json(trackedOrders.get(orderNumber) ?? testOrder)
    }
  ),

  http.get('http://localhost:8000/api/orders/track/', ({ request }) => {
    const url = new URL(request.url)
    const orderNumber = url.searchParams.get('order_number')

    if (!orderNumber) {
      return HttpResponse.json(
        { detail: 'Debes indicar el número de pedido.' },
        { status: 400 }
      )
    }

    const order = trackedOrders.get(orderNumber)
    if (order) {
      return HttpResponse.json(order)
    }

    return HttpResponse.json(testOrder)
  }),
]
