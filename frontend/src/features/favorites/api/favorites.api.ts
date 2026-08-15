import type { components } from '@/api/schema.d.ts'
import { apiClient } from '@/lib/api-client'

export type Favorite = components['schemas']['Favorite']

export async function getFavorites(): Promise<Favorite[]> {
  const { data, error } = await apiClient.GET('/api/favorites/')
  if (error) throw new Error('No se pudieron cargar los favoritos'); return data ?? []
}
export async function mergeFavorites(productIds: number[]): Promise<Favorite[]> {
  const { data, error } = await apiClient.POST('/api/favorites/', { body: { product_ids: productIds } })
  if (error) throw new Error('No se pudieron sincronizar los favoritos'); return data ?? []
}
export async function deleteFavorite(productId: number): Promise<void> {
  const { error } = await apiClient.DELETE('/api/favorites/{product_id}/', { params: { path: { product_id: productId } } })
  if (error) throw new Error('No se pudo quitar el favorito')
}
