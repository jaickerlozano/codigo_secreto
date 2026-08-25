import type { Comuna, Region } from '@/features/shipping/types'

import type { AddressData } from '../types'

export type ShippingDestination = {
  comunaId: number
  comunaName: string
  regionName: string
}

export type ShippingDestinationResolution =
  | { status: 'pending' }
  | { status: 'invalid' }
  | { status: 'valid'; destination: ShippingDestination }

// Labels in checkout state are only a snapshot. Resolve them from the current
// catalog before they can be displayed or used for a shipping request.
export function reconcileShippingDestination(
  address: AddressData,
  regions: Region[] | undefined,
  comunas: Comuna[] | undefined
): ShippingDestinationResolution {
  if (address.regionId <= 0 || address.comunaId <= 0) {
    return { status: 'invalid' }
  }

  if (regions === undefined) {
    return { status: 'pending' }
  }

  const region = regions.find((candidate) => candidate.id === address.regionId)
  if (!region) {
    return { status: 'invalid' }
  }

  if (comunas === undefined) {
    return { status: 'pending' }
  }

  const comuna = comunas.find((candidate) => candidate.id === address.comunaId)
  if (!comuna) {
    return { status: 'invalid' }
  }

  return {
    status: 'valid',
    destination: {
      comunaId: comuna.id,
      comunaName: comuna.name,
      regionName: region.name,
    },
  }
}
