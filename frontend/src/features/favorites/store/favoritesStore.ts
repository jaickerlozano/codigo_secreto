import { create } from 'zustand'

export const FAVORITES_STORAGE_KEY = 'cs-favorites'
export function readGuestFavoriteIds(): number[] { try { const parsed: unknown = JSON.parse(localStorage.getItem(FAVORITES_STORAGE_KEY) ?? '[]'); return Array.isArray(parsed) ? parsed.filter((id): id is number => typeof id === 'number' && Number.isInteger(id)) : [] } catch { return [] } }
function persistGuestIds(ids: number[]): void { try { localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(ids)) } catch { /* Storage unavailable — in-memory only. */ } }
interface FavoritesState {
  ids: number[]
  initFromStorage: () => void
  toggleId: (productId: number) => void
  removeId: (productId: number) => void
  clearIds: () => void
}
export const useFavoritesStore = create<FavoritesState>((set) => ({
  ids: readGuestFavoriteIds(),
  initFromStorage: () => set({ ids: readGuestFavoriteIds() }),
  toggleId: (productId) => set((state) => {
    const ids = state.ids.includes(productId) ? state.ids.filter((id) => id !== productId) : [...state.ids, productId]
    persistGuestIds(ids)
    return { ids }
  }),
  removeId: (productId) => set((state) => {
    const ids = state.ids.filter((id) => id !== productId)
    persistGuestIds(ids)
    return { ids }
  }),
  clearIds: () => { try { localStorage.removeItem(FAVORITES_STORAGE_KEY) } catch { /* ignore */ } set({ ids: [] }) },
}))
export function clearGuestFavoriteIds(): void { useFavoritesStore.getState().clearIds() }
