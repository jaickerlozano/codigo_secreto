import { useQuery } from '@tanstack/react-query'

import { getRegions } from '../api/shipping.api'
import type { Region } from '../types'

export function useRegions() {
  return useQuery<Region[], Error>({
    queryKey: ['regions'],
    queryFn: getRegions,
    staleTime: 1000 * 60 * 10,
  })
}
