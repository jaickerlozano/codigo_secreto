import { useQuery } from '@tanstack/react-query'

import { listOrders, type OrdersResponse } from '../api/orders.api'

const ORDERS_PAGE = 1

export function useOrders() {
  return useQuery<OrdersResponse, Error>({
    queryKey: ['orders', ORDERS_PAGE],
    queryFn: () => listOrders(ORDERS_PAGE),
    retry: 1,
    staleTime: 1000 * 60 * 2,
  })
}
