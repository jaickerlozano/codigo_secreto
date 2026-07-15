import { useMutation } from '@tanstack/react-query'

import {
  initiatePayment,
  type InitiatePaymentInput,
  type PaymentInitiation,
} from '../api/payments.api'

export function useInitiatePayment() {
  return useMutation<PaymentInitiation, Error, InitiatePaymentInput>({
    mutationFn: initiatePayment,
  })
}
