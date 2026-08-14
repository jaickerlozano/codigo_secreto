import { apiClient } from '@/lib/api-client'
import type { components } from '@/api/schema.d.ts'

export type PaymentInitiation = components['schemas']['InitiatePaymentResponse']
export type ApprovePaymentResult = components['schemas']['MockApproveResponse']
export type InitiatePaymentInput = components['schemas']['InitiatePayment']

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

export async function initiatePayment(input: InitiatePaymentInput): Promise<PaymentInitiation> {
  const { data, error } = await apiClient.POST('/api/payments/initiate/', { body: input })
  if (error || !data) throw new Error(extractErrorMessage(error))
  return data
}

export async function approvePayment(transactionId: number): Promise<ApprovePaymentResult> {
  const { data, error } = await apiClient.POST('/api/payments/{transaction_id}/mock-approve/', { params: { path: { transaction_id: transactionId } } })
  if (error || !data) throw new Error(extractErrorMessage(error))
  return data
}
