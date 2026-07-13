import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { Category } from '../types'
import { mapApiCategory } from '../lib/mappers'

export function useCategories() {
  return useQuery<Category[], Error>({
    queryKey: ['categories'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/categories/')

      if (error) {
        throw new Error(
          typeof error === 'object' &&
            error !== null &&
            'message' in error
            ? String((error as { message?: unknown }).message)
            : 'Error cargando categorías',
        )
      }

      if (!data) {
        throw new Error('No se recibieron categorías')
      }

      return data.results.map(mapApiCategory)
    },
  })
}
