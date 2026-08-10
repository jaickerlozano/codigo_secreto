import { useQuery, useQueryClient } from '@tanstack/react-query'; import { useEffect, useMemo, useRef } from 'react'

import { getGuestQuote, guestQuoteQueryKey, shouldRetryGuestQuote, type GuestQuote, type GuestQuoteInput } from '../api/quote.api'

export function useGuestQuote(input: GuestQuoteInput) {
  const queryClient = useQueryClient()
  const key = useMemo(() => guestQuoteQueryKey(input), [input])
  const keyIdentity = JSON.stringify(key)
  const previousKey = useRef<{ identity: string; key: typeof key } | null>(null)

  useEffect(() => { if (previousKey.current && previousKey.current.identity !== keyIdentity) void queryClient.cancelQueries({ queryKey: previousKey.current.key, exact: true }); previousKey.current = { identity: keyIdentity, key } }, [key, keyIdentity, queryClient])

  return useQuery<GuestQuote, Error>({ queryKey: key, queryFn: ({ signal }) => getGuestQuote(input, signal), enabled: input.items.length > 0, retry: shouldRetryGuestQuote, staleTime: 1000 * 60 * 10, refetchOnWindowFocus: false })
}
