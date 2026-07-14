import { useQuery } from '@tanstack/react-query'

import { getComunas } from '../api/shipping.api'
import type { Comuna } from '../types'

export interface UseComunasOptions {
  enabled?: boolean
}

export function useComunas(
  regionId?: number,
  options: UseComunasOptions = {},
) {
  return useQuery<Comuna[], Error>({
    queryKey: ['comunas', regionId],
    queryFn: () => getComunas(regionId),
    enabled: options.enabled ?? true,
    staleTime: 1000 * 60 * 10,
  })
}
