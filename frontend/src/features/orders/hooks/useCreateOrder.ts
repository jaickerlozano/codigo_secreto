import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createOrder, type CreateOrderInput, type Order } from '../api/orders.api'
import { invalidateOrderWorkflow } from '../lib/pending-order'

export function useCreateOrder() {
  const client = useQueryClient()
  return useMutation<Order, Error, CreateOrderInput>({
    mutationFn: createOrder,
    onSuccess: () => invalidateOrderWorkflow(client),
  })
}
