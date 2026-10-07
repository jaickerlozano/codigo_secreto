import { useLayoutEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '@/features/auth'
import { getPendingOrder } from '../api/orders.api'
import { pendingOrderScope } from '../lib/pending-order'

export function usePendingOrder() {
  const client = useQueryClient()
  const { user, isLoading, authError, retryAuth } = useAuth()
  const ready = !isLoading && !authError
  const actor = ready ? (user ? `user:${user.id}` : 'guest') : 'unresolved'
  const { generation } = pendingOrderScope(client, actor)
  useLayoutEffect(() => {
    const stale = { predicate: (query: { queryKey: readonly unknown[] }) => query.queryKey[0] === 'pending-order' && query.queryKey[1] !== generation }
    void client.cancelQueries(stale)
    client.removeQueries(stale)
  }, [client, generation])
  const query = useQuery({
    queryKey: ['pending-order', generation],
    queryFn: ({ signal }) => getPendingOrder(signal),
    enabled: ready,
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: true,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  })
  return {
    ...query,
    actorScope: generation,
    isAuthLoading: isLoading,
    authError,
    data: ready ? query.data : undefined,
    discoveryError: authError ?? query.error,
    isDiscovering: isLoading || (ready && query.isPending),
    isResolved: ready && query.isSuccess && !query.isFetching,
    retryDiscovery: () => authError ? retryAuth() : query.refetch(),
  }
}
