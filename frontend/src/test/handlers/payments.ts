import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'
import { trackedOrders } from './orders'

let transactionOrders = new Map<number, number>()

export function resetPaymentHandlers(): void {
  transactionOrders = new Map<number, number>()
}

export const paymentHandlers = [
  http.post('http://localhost:8000/api/payments/initiate/', async ({ request }) => {
    const body = (await request.json()) as components['schemas']['InitiatePayment']
    const token = `token_simulado_cl_f_${body.order_id}x99`
    transactionOrders.set(1, body.order_id)
    return HttpResponse.json({ transaction_id: 1, order_id: body.order_id, amount: 29990, payment_url: `https://api.tu_pasarela.cl/mock-checkout?token=${token}`, gateway_reference: token })
  }),

  http.post('http://localhost:8000/api/payments/:transactionId/mock-approve/', ({ params }) => {
    const entry = [...trackedOrders].find(([, existing]) => existing.id === transactionOrders.get(Number(params.transactionId)))
    if (!entry) return HttpResponse.json({ detail: 'Not found.' }, { status: 404 })
    const [number, existing] = entry
    trackedOrders.set(number, { ...existing, status: 'PAID' })
    return HttpResponse.json({ transaction_id: Number(params.transactionId), order_id: existing.id, status: 'APPROVED', order_status: 'PAID' })
  }),
]
