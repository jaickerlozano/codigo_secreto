import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { operations } from '@/api/schema.d.ts'
import type { Product } from '../types'
import { mapApiProduct } from '../lib/mappers'

export interface UseProductsFilters {
  page?: number
  pageSize?: number
  category?: number
  search?: string
  minPrice?: number
  maxPrice?: number
}

interface ProductsResponse {
  count: number
  next: string | null
  previous: string | null
  results: Product[]
}

export function useProducts(filters: UseProductsFilters = {}) {
  const {
    page = 1,
    pageSize = 12,
    category,
    search,
    minPrice,
    maxPrice,
  } = filters

  return useQuery<ProductsResponse, Error>({
    queryKey: ['products', filters],
    queryFn: async () => {
      const query = {
        page,
        page_size: pageSize,
        ...(category !== undefined && { category }),
        ...(search && { search }),
        ...(minPrice !== undefined && { min_price: minPrice }),
        ...(maxPrice !== undefined && { max_price: maxPrice }),
      } as unknown as NonNullable<
        operations['products_list']['parameters']['query']
      >

      const { data, error } = await apiClient.GET('/api/products/', {
        params: { query },
      })

      if (error) {
        throw new Error(
          typeof error === 'object' &&
            error !== null &&
            'message' in error
            ? String((error as { message?: unknown }).message)
            : 'Error cargando productos',
        )
      }

      if (!data) {
        throw new Error('No se recibieron productos')
      }

      return {
        count: data.count,
        next: data.next ?? null,
        previous: data.previous ?? null,
        results: data.results.map((apiProduct) =>
          mapApiProduct(apiProduct),
        ),
      }
    },
  })
}
