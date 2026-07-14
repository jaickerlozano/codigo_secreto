import { apiClient } from '@/lib/api-client'

export interface PaymentInitiation {
  transaction_id: number
  order_id: number
  amount: number
  payment_url: string
  gateway_reference: string
}

export interface InitiatePaymentInput {
  order_id: number
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

export async function initiatePayment(
  input: InitiatePaymentInput,
): Promise<PaymentInitiation> {
  const { data, error } = await apiClient.POST('/api/payments/initiate/', {
    body: input,
  })

  if (error) {
    throw new Error(extractErrorMessage(error))
  }

  // The generated OpenAPI schema does not declare the response body for this
  // endpoint, but the backend returns the shape defined in PaymentInitiation.
  return (data ?? {}) as PaymentInitiation
}
