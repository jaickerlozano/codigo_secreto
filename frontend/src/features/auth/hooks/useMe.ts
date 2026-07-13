import { useQuery } from '@tanstack/react-query'

import { getMe } from '../api/auth.api'
import type { UserMe } from '../types'

export function useMe() {
  return useQuery<UserMe | null, Error>({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
    staleTime: 1000 * 60 * 5,
    refetchOnWindowFocus: false,
  })
}
