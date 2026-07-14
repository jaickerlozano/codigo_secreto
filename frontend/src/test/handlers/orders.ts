import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Order = components['schemas']['Order']
type CreateOrderInput = components['schemas']['Order']

let nextOrderId = 100

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
]
