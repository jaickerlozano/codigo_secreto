import { http, HttpResponse } from 'msw'

export const paymentHandlers = [
  http.post('*api/payments/initiate/', async ({ request }) => {
    const body = (await request.json()) as { order_id: number }
    const token = `token_simulado_cl_f_${body.order_id}x99`

    return HttpResponse.json({
      transaction_id: 1,
      order_id: body.order_id,
      amount: 29990,
      payment_url: `https://api.tu_pasarela.cl/mock-checkout?token=${token}`,
      gateway_reference: token,
    })
  }),
]
