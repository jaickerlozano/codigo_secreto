import type { QueryClient } from '@tanstack/react-query'

import { mergeFavorites } from '../api/favorites.api'
import { clearGuestFavoriteIds } from '../store/favoritesStore'

/** Merges guest favorites after login; guest ids are cleared ONLY after success. */
export async function mergeFavoritesOnLogin(guestIds: number[], queryClient: QueryClient): Promise<void> {
  if (guestIds.length > 0) await mergeFavorites(guestIds); clearGuestFavoriteIds(); void queryClient.invalidateQueries({ queryKey: ['favorites'] })
}
