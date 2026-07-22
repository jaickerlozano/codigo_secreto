// src/hooks/useProducts.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { operations } from '@/api/schema.d.ts'
import type { Product } from '../types'
import { mapApiProduct } from '../lib/mappers'

export interface UseProductsFilters {
  page?: number
  category?: number
  search?: string
  minPrice?: number
  maxPrice?: number
  ordering?: string
  experienceLevel?: number
  experienceLevelGte?: number
  experienceLevelLte?: number
  supplier?: number
}

interface ProductsResponse {
  count: number
  next: string | null
  previous: string | null
  results: Product[]
}

export function useProducts(filters: UseProductsFilters = {}) {
  //  CORRECCIÓN 1: Extraemos 'ordering' de los filtros recibidos
  const {
    page = 1,
    category,
    search,
    minPrice,
    maxPrice,
    ordering,
    experienceLevel,
    experienceLevelGte,
    experienceLevelLte,
    supplier,
  } = filters

  return useQuery<ProductsResponse, Error>({
    //  CORRECCIÓN 2: Añadimos 'ordering' a la queryKey. 
    // Así, si el usuario cambia el orden, React Query sabe que debe invalidar la caché y pedir datos nuevos.
    queryKey: [
      'products', 
      { 
        page, 
        category, 
        search, 
        minPrice, 
        maxPrice, 
        ordering,
        experienceLevel, 
        supplier 
      }
    ],
    queryFn: async () => {
      //  CORRECCIÓN 3: Mapeamos la propiedad 'ordering' hacia el objeto de consulta de la API
      const query = {
        page,
        ...(ordering && { ordering }), // Envía ?ordering=-id, ?ordering=price, etc.
        ...(category !== undefined && { category }),
        ...(search && { search }),
        ...(minPrice !== undefined && { min_price: String(minPrice) }),
        ...(maxPrice !== undefined && { max_price: String(maxPrice) }),
        ...(experienceLevel !== undefined && { experience_level: experienceLevel }),
        ...(experienceLevelGte !== undefined && { experience_level__gte: experienceLevelGte }),
        ...(experienceLevelLte !== undefined && { experience_level__lte: experienceLevelLte }),
        ...(supplier !== undefined && { supplier }),
      } satisfies NonNullable<operations['products_list']['parameters']['query']>

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
