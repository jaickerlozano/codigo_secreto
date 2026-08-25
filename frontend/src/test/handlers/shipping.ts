import { http, HttpResponse } from 'msw'

import type { operations } from '@/api/schema'

type RegionsResponse =
  operations['shipping_regions_list']['responses'][200]['content']['application/json']
type RegionFixture = Pick<
  RegionsResponse[number],
  'id' | 'name' | 'ordinal_number'
>
type ComunasRequest = NonNullable<
  operations['shipping_comunas_list']['parameters']['query']
>
type ComunasResponse =
  operations['shipping_comunas_list']['responses'][200]['content']['application/json']
type DispatchOptionsRequest =
  operations['shipping_dispatch_options_retrieve']['parameters']['query']
type DispatchOptionsResponse =
  operations['shipping_dispatch_options_retrieve']['responses'][200]['content']['application/json']

const testRegions: RegionFixture[] = [
  { id: 13, name: 'Región Metropolitana', ordinal_number: 7 },
  { id: 5, name: 'Valparaíso', ordinal_number: 4 },
]

const testComunas: ComunasResponse = [
  { id: 1, name: 'Santiago', shipping_cost: 3500, is_active: true },
  { id: 2, name: 'Providencia', shipping_cost: 3500, is_active: true },
  ...Array.from({ length: 10 }, (_, index) => ({
    id: index + 3,
    name: `Comuna Metropolitana ${String(index + 1).padStart(2, '0')}`,
    shipping_cost: 3500,
    is_active: true,
  })),
  { id: 13, name: 'Viña del Mar', shipping_cost: 4000, is_active: true },
]

export const shippingHandlers = [
  http.get(/\/api\/shipping\/regions\/$/, () =>
    HttpResponse.json(testRegions),
  ),

  http.get(/\/api\/shipping\/comunas\/$/, ({ request }) => {
    const url = new URL(request.url)
    const regionParam = url.searchParams.get('region')
    const query: ComunasRequest = {
      region: regionParam ? parseInt(regionParam, 10) : undefined,
    }
    const regionId = query.region ?? null

    const filtered =
      regionId === null
        ? testComunas
        : testComunas.filter((comuna) => {
            if (regionId === 13) {
              return comuna.id !== 13
            }
            if (regionId === 5) {
              return comuna.id === 13
            }
            return false
          })

    return HttpResponse.json(filtered)
  }),

  http.get(/\/api\/shipping\/dispatch-options\/$/, ({ request }) => {
    const url = new URL(request.url)
    const query: DispatchOptionsRequest = {
      comuna: parseInt(url.searchParams.get('comuna') ?? '0', 10),
    }
    const comunaId = query.comuna

    if (comunaId === 1) {
      const response: DispatchOptionsResponse = {
        comuna_id: comunaId,
        mode: 'santiago',
        dates: ['2026-08-25', '2026-08-27'],
        shipping_option: null,
      }
      return HttpResponse.json(response)
    }

    const response: DispatchOptionsResponse = {
      comuna_id: comunaId,
      mode: 'regional',
      dates: null,
      shipping_option: {
        shipping_option_id: 7,
        key: 'chilexpress',
        carrier: 'Chilexpress',
        min_lead_days: 2,
        max_lead_days: 4,
      },
    }
    return HttpResponse.json(response)
  }),
]
