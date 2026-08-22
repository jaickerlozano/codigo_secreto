import type { components } from '@/api/schema.d.ts'

import type { Comuna, DispatchOptions, Region } from '../types'

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

export function mapApiDispatchOptions(
  api: components['schemas']['DispatchOptions'],
): DispatchOptions {
  return {
    comunaId: api.comuna_id,
    mode: api.mode,
    dates: api.dates,
    shippingOption: api.shipping_option
      ? {
          shippingOptionId: api.shipping_option.shipping_option_id,
          key: api.shipping_option.key,
          carrier: api.shipping_option.carrier,
          tariff: api.shipping_option.tariff,
          minLeadDays: api.shipping_option.min_lead_days,
          maxLeadDays: api.shipping_option.max_lead_days,
        }
      : null,
  }
}
