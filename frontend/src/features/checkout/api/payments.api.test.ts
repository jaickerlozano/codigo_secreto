import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { server } from '@/test/setup'

import { clampPollIntervalSeconds, DEFAULT_POLL_SECONDS, initiatePayment, MAX_POLL_SECONDS, MIN_POLL_SECONDS, SpecialDeliveryAgreementRequiredError } from './payments.api'

describe('clampPollIntervalSeconds', () => {
  it('keeps a backend interval inside the bounded range', () => {
    expect(clampPollIntervalSeconds(30)).toBe(30)
  })
  it('clamps very fast polling up to the minimum', () => {
    expect(clampPollIntervalSeconds(1)).toBe(MIN_POLL_SECONDS)
  })
  it('clamps very slow polling down to the maximum', () => {
    expect(clampPollIntervalSeconds(9999)).toBe(MAX_POLL_SECONDS)
  })
  it('falls back to the default for non-finite values', () => {
    expect(clampPollIntervalSeconds(Number.NaN)).toBe(DEFAULT_POLL_SECONDS)
    expect(clampPollIntervalSeconds(Number.POSITIVE_INFINITY)).toBe(DEFAULT_POLL_SECONDS)
  })
})

describe('initiatePayment', () => {
  it('throws the typed agreement error and sends a stable per-order idempotency key', async () => {
    let seenKey: string | null = null
    server.use(
      http.post('http://localhost:8000/api/payments/initiate/', async ({ request }) => {
        seenKey = request.headers.get('Idempotency-Key')
        return HttpResponse.json({ code: 'special_delivery_agreement_required', detail: 'Coordina tu entrega especial por WhatsApp antes de pagar.', whatsapp_url: 'https://wa.me/56912345678?text=Hola', poll_after_seconds: 30 }, { status: 409 })
      }),
    )

    const promise = initiatePayment({ order_id: 123 })
    await expect(promise).rejects.toBeInstanceOf(SpecialDeliveryAgreementRequiredError)
    expect(seenKey).toBe('payment-123')
    await promise.catch((error: unknown) => {
      if (error instanceof SpecialDeliveryAgreementRequiredError) {
        expect(error.whatsappUrl).toBe('https://wa.me/56912345678?text=Hola')
        expect(error.pollAfterSeconds).toBe(30)
        expect(error.code).toBe('special_delivery_agreement_required')
      }
    })
  })

  it('keeps a generic error for non-agreement failures', async () => {
    server.use(
      http.post('http://localhost:8000/api/payments/initiate/', () => HttpResponse.json({ order_id: ['Este pedido ya fue pagado.'] }, { status: 400 })),
    )
    await expect(initiatePayment({ order_id: 123 })).rejects.toThrow('Este pedido ya fue pagado.')
  })
})