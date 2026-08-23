import { http, HttpResponse } from 'msw'

const testRegions = [
  { id: 13, name: 'Región Metropolitana', ordinal_number: 7 },
  { id: 5, name: 'Valparaíso', ordinal_number: 4 },
]

const testComunas = [
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
    const regionId = regionParam ? parseInt(regionParam, 10) : null

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
    const comunaId = parseInt(url.searchParams.get('comuna') ?? '0', 10)

    if (comunaId === 1) {
      return HttpResponse.json({
        comuna_id: comunaId,
        mode: 'santiago',
        dates: ['2026-08-25', '2026-08-27'],
        shipping_option: null,
      })
    }

    return HttpResponse.json({
      comuna_id: comunaId,
      mode: 'regional',
      dates: null,
      shipping_option: {
        shipping_option_id: 7,
        key: 'chilexpress',
        carrier: 'Chilexpress',
        tariff: 4900,
        min_lead_days: 2,
        max_lead_days: 4,
      },
    })
  }),
]
