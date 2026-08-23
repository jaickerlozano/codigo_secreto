import type { operations } from '@/api/schema.d.ts'
import { apiClient } from '@/lib/api-client'

import { mapApiComuna, mapApiDispatchOptions, mapApiRegion } from '../lib/mappers'
import type { Comuna, DispatchOptions, Region } from '../types'

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

  return data.map(mapApiRegion)
}

export async function getComunas(regionId?: number): Promise<Comuna[]> {
  const query: NonNullable<
    operations['shipping_comunas_list']['parameters']['query']
  > = regionId === undefined ? {} : { region: regionId }

  const { data, error } = await apiClient.GET('/api/shipping/comunas/', {
    params: {
      query,
    },
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data.map(mapApiComuna)
}

export async function getDispatchOptions(comunaId: number): Promise<DispatchOptions> {
  const { data, error } = await apiClient.GET('/api/shipping/dispatch-options/', {
    params: {
      query: { comuna: comunaId },
    },
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return mapApiDispatchOptions(data)
}
