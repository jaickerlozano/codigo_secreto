import { useMutation, useQueryClient } from '@tanstack/react-query'

import { cancelOrder } from '../api/orders.api'
import { invalidateOrderWorkflow } from '../lib/pending-order'

export function useCancelOrder() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: cancelOrder,
    onSuccess: (order) => {
      client.setQueryData(['order', order.order_number], order)
    },
    // A stale 409 must refresh the actual state as well as availability.
    onSettled: () => invalidateOrderWorkflow(client),
    retry: false,
  })
}
