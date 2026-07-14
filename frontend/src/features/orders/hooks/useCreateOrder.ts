import { useMutation } from '@tanstack/react-query'

import { createOrder, type CreateOrderInput, type Order } from '../api/orders.api'

export function useCreateOrder() {
  return useMutation<Order, Error, CreateOrderInput>({
    mutationFn: createOrder,
  })
}
