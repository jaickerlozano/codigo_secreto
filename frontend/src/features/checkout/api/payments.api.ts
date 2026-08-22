import { apiClient } from '@/lib/api-client'
import type { components } from '@/api/schema.d.ts'

export type PaymentInitiation = components['schemas']['InitiatePaymentResponse']
export type ApprovePaymentResult = components['schemas']['MockApproveResponse']
export type InitiatePaymentInput = components['schemas']['InitiatePayment']

/** Bounds for the special-delivery agreement gate poll, in seconds. */
export const MIN_POLL_SECONDS = 5
export const MAX_POLL_SECONDS = 300
export const DEFAULT_POLL_SECONDS = 30

/** Typed 409 recovery body, generated from the backend Spectacular schema. */
export type SpecialDeliveryAgreementPayload = components['schemas']['SpecialDeliveryAgreementRequiredError']

export class SpecialDeliveryAgreementRequiredError extends Error {
  readonly code = 'special_delivery_agreement_required' as const
  readonly whatsappUrl: string
  readonly pollAfterSeconds: number

  constructor(payload: SpecialDeliveryAgreementPayload) {
    super(payload.detail)
    this.name = 'SpecialDeliveryAgreementRequiredError'
    this.whatsappUrl = payload.whatsapp_url
    this.pollAfterSeconds = payload.poll_after_seconds
  }
}

export function isSpecialDeliveryAgreementError(error: unknown): error is SpecialDeliveryAgreementRequiredError {
  return error instanceof SpecialDeliveryAgreementRequiredError
}

export function clampPollIntervalSeconds(seconds: number): number {
  if (!Number.isFinite(seconds)) return DEFAULT_POLL_SECONDS
  return Math.min(MAX_POLL_SECONDS, Math.max(MIN_POLL_SECONDS, Math.round(seconds)))
}

function extractErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail
    }
    if ('message' in error && typeof error.message === 'string') {
      return error.message
    }
    const messages = Object.values(error).flat()
    if (messages.length > 0 && typeof messages[0] === 'string') {
      return messages[0]
    }
  }
  return 'Ocurrió un error al iniciar el pago. Inténtalo de nuevo.'
}

function isSpecialDeliveryAgreementPayload(error: unknown): error is SpecialDeliveryAgreementPayload {
  if (typeof error !== 'object' || error === null) return false
  const candidate = error as Record<string, unknown>
  // Runtime guard narrowing the generated type: only the exact backend code
  // with the recovery fields may be treated as the typed agreement payload.
  return (
    candidate.code === 'special_delivery_agreement_required' &&
    typeof candidate.detail === 'string' &&
    typeof candidate.whatsapp_url === 'string' &&
    typeof candidate.poll_after_seconds === 'number'
  )
}

export async function initiatePayment(input: InitiatePaymentInput): Promise<PaymentInitiation> {
  const { data, error } = await apiClient.POST('/api/payments/initiate/', {
    body: input,
    // Stable per-order key so a retry replays the same PENDING attempt
    // instead of creating a duplicate transaction.
    params: { header: { 'Idempotency-Key': `payment-${input.order_id}` } },
  })
  if (error || !data) {
    if (isSpecialDeliveryAgreementPayload(error)) {
      throw new SpecialDeliveryAgreementRequiredError(error)
    }
    throw new Error(extractErrorMessage(error))
  }
  return data
}

export async function approvePayment(transactionId: number): Promise<ApprovePaymentResult> {
  const { data, error } = await apiClient.POST('/api/payments/{transaction_id}/mock-approve/', { params: { path: { transaction_id: transactionId } } })
  if (error || !data) throw new Error(extractErrorMessage(error))
  return data
}
