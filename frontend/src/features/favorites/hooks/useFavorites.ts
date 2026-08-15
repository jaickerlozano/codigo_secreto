import { useQueries, useQuery } from '@tanstack/react-query'

import { useAuth } from '@/features/auth/context/AuthContext'
import type { Product } from '@/features/catalog/types'
import { mapApiProduct } from '@/features/catalog/lib/mappers'
import { apiClient } from '@/lib/api-client'

import { getFavorites } from '../api/favorites.api'
import { useFavoritesStore } from '../store/favoritesStore'

export function useFavorites() {
  const { isAuthenticated } = useAuth()
  return useQuery({ queryKey: ['favorites'], queryFn: getFavorites, enabled: isAuthenticated })
}
export function useFavoriteProducts(ids: number[]) {
  const uniqueIds = Array.from(new Set(ids))
  const queries = useQueries({ queries: uniqueIds.map((id) => ({ queryKey: ['product', id], queryFn: async (): Promise<Product> => { const { data, error } = await apiClient.GET('/api/products/{id}/', { params: { path: { id } } }); if (error || !data) throw new Error('No se pudo cargar el producto'); return mapApiProduct(data) } })) })
  return queries.map((query, index) => ({ id: uniqueIds[index], ...query }))
}
export function useFavoriteCount(): number | null {
  const { isAuthenticated, isLoading, authError } = useAuth()
  const guestIds = useFavoritesStore((s) => s.ids)
  const { data, isError, isFetching } = useFavorites()
  if (isLoading || authError) return null; return !isAuthenticated ? guestIds.length : isError || isFetching || !data ? null : data.length
}
