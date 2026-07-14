import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Order = components['schemas']['Order']
type CreateOrderInput = components['schemas']['Order']

let nextOrderId = 100

export const testOrder: Order = {
  id: 123,
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
  subtotal: 29990,
  shipping_cost: 0,
  total: 29990,
  status: 'PENDING',
  created_at: '2026-07-14T10:30:00Z',
  items: [
    {
      id: 1,
      product_id: 1,
      product_name: 'Vibrador de prueba',
      price: 29990,
      quantity: 1,
      subtotal: '29990',
    },
  ],
}

export const orderHandlers = [
  http.post('*api/orders/', async ({ request }) => {
    const body = (await request.json()) as CreateOrderInput
    const order: Order = {
      id: nextOrderId++,
      order_number: `CS-${Math.floor(100000 + Math.random() * 900000)}`,
      phone: body.phone,
      shipping_address: body.shipping_address,
      apartment_office: body.apartment_office ?? null,
      guest_email: body.guest_email ?? null,
      guest_name: body.guest_name ?? null,
      comuna: body.comuna,
      comuna_name: body.comuna_name,
      region_name: body.region_name,
      payment_method: body.payment_method ?? 'webpay',
      subtotal: 29990,
      shipping_cost: 0,
      total: 29990,
      status: 'PENDING',
      created_at: new Date().toISOString(),
      items: [],
    }
    return HttpResponse.json(order, { status: 201 })
  }),

  http.get('*api/orders/:id/', () => HttpResponse.json(testOrder)),
]
