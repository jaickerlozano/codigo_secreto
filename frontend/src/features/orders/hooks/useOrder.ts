import { useQuery } from '@tanstack/react-query'

import { getOrder, type Order } from '../api/orders.api'

export function useOrder(orderNumber: string | undefined) {
  return useQuery<Order, Error>({
    queryKey: ['order', orderNumber],
    queryFn: () => getOrder(orderNumber!),
    enabled: !!orderNumber,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
    retry: 1,
    staleTime: 1000 * 60 * 2,
  })
}
