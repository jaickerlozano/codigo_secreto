import type { components } from '@/api/schema.d.ts'

import type { Comuna, Region } from '../types'

export function mapApiRegion(
  apiRegion: components['schemas']['Region'],
): Region {
  return {
    id: apiRegion.id,
    name: apiRegion.name,
    ordinalNumber: apiRegion.ordinal_number,
  }
}

export function mapApiComuna(
  apiComuna: components['schemas']['Comuna'],
): Comuna {
  return {
    id: apiComuna.id,
    name: apiComuna.name,
    shippingCost: apiComuna.shipping_cost,
    isActive: apiComuna.is_active,
  }
}
