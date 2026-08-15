import { QueryClient } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'

import { trackedFavorites } from '@/test/handlers/favorites'
import { server } from '@/test/setup'

import { mergeFavoritesOnLogin } from './lib/mergeFavoritesOnLogin'
import { FAVORITES_STORAGE_KEY, readGuestFavoriteIds, useFavoritesStore } from './store/favoritesStore'

const FAVORITES_URL = 'http://localhost:8000/api/favorites/'

describe('favoritesStore (guest cs-favorites ids)', () => {
  beforeEach(() => { window.localStorage.clear(); useFavoritesStore.getState().initFromStorage() })
  it('starts empty, then persists only product ids on toggle', () => {
    expect(useFavoritesStore.getState().ids).toEqual([]); useFavoritesStore.getState().toggleId(42); useFavoritesStore.getState().toggleId(7)
    expect(useFavoritesStore.getState().ids).toEqual([42, 7]); expect(JSON.parse(window.localStorage.getItem(FAVORITES_STORAGE_KEY) ?? '[]')).toEqual([42, 7])
  })
  it('toggling an existing id removes it and persists the change', () => {
    useFavoritesStore.getState().toggleId(42); useFavoritesStore.getState().toggleId(42); expect(useFavoritesStore.getState().ids).toEqual([]); expect(JSON.parse(window.localStorage.getItem(FAVORITES_STORAGE_KEY) ?? '[]')).toEqual([])
  })
  it('ignores non-integer values so storage never holds tokens or session data', () => {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1, 'access-token', 2.5, 'refresh']))
    expect(readGuestFavoriteIds()).toEqual([1])
  })
})

describe('mergeFavoritesOnLogin', () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  beforeEach(() => window.localStorage.clear())
  afterEach(() => queryClient.clear())
  it('merges guest ids into the backend and clears guest storage only after success', async () => {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1, 2])); await mergeFavoritesOnLogin([1, 2], queryClient)
    expect(trackedFavorites.map((f) => f.product)).toEqual([1, 2]); expect(window.localStorage.getItem(FAVORITES_STORAGE_KEY)).toBeNull()
  })
  it('deduplicates guest ids against existing server favorites', async () => {
    await mergeFavoritesOnLogin([1], queryClient); window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1, 2]))
    await mergeFavoritesOnLogin([1, 2], queryClient)
    expect(trackedFavorites.map((f) => f.product)).toEqual([1, 2])
  })
  it('does not call the merge endpoint when there are no guest ids', async () => {
    let calls = 0; server.use(http.post(FAVORITES_URL, () => { calls += 1; return HttpResponse.json([]) }))
    await mergeFavoritesOnLogin([], queryClient)
    expect(calls).toBe(0); expect(window.localStorage.getItem(FAVORITES_STORAGE_KEY)).toBeNull()
  })
  it('keeps guest ids when the merge fails so they can merge on the next login', async () => {
    server.use(http.post(FAVORITES_URL, () => HttpResponse.json({ detail: 'boom' }, { status: 500 }))); window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1]))
    await expect(mergeFavoritesOnLogin([1], queryClient)).rejects.toThrow()
    expect(window.localStorage.getItem(FAVORITES_STORAGE_KEY)).toBe('[1]'); expect(trackedFavorites).toEqual([])
  })
})
