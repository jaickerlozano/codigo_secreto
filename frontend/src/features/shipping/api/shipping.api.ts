import type { operations } from '@/api/schema.d.ts'
import { apiClient } from '@/lib/api-client'

import { mapApiComuna, mapApiRegion } from '../lib/mappers'
import type { Comuna, Region } from '../types'

function extractErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail
    }
    if ('message' in error && typeof error.message === 'string') {
      return error.message
    }
  }
  return 'Ocurrió un error cargando datos de envío.'
}

export async function getRegions(): Promise<Region[]> {
  const { data, error } = await apiClient.GET('/api/shipping/regions/')

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data.results.map(mapApiRegion)
}

export async function getComunas(regionId?: number): Promise<Comuna[]> {
  const query: Record<string, number> = {}

  if (regionId !== undefined) {
    query.region = regionId
  }

  const { data, error } = await apiClient.GET('/api/shipping/comunas/', {
    params: {
      query: query as unknown as NonNullable<
        operations['shipping_comunas_list']['parameters']['query']
      >,
    },
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data.results.map(mapApiComuna)
}
