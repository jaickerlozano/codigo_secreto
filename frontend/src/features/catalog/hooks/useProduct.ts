import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { Product } from '../types'
import { mapApiProduct } from '../lib/mappers'

export function useProduct(id: number) {
  return useQuery<Product, Error>({
    queryKey: ['product', id],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/products/{id}/', {
        params: { path: { id } },
      })

      if (error) {
        throw new Error(
          typeof error === 'object' &&
            error !== null &&
            'message' in error
            ? String((error as { message?: unknown }).message)
            : 'Error cargando el producto',
        )
      }

      if (!data) {
        throw new Error('Producto no encontrado')
      }

      return mapApiProduct(data)
    },
    enabled: Boolean(id),
  })
}
