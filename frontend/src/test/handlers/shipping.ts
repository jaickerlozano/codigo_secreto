import { http, HttpResponse } from 'msw'

const testRegions = [
  { id: 13, name: 'Región Metropolitana', ordinal_number: 7 },
  { id: 5, name: 'Valparaíso', ordinal_number: 4 },
]

const testComunas = [
  { id: 1, name: 'Santiago', shipping_cost: 3500, is_active: true },
  { id: 2, name: 'Providencia', shipping_cost: 3500, is_active: true },
  { id: 3, name: 'Viña del Mar', shipping_cost: 4000, is_active: true },
]

export const shippingHandlers = [
  http.get('*api/shipping/regions/', () =>
    HttpResponse.json({
      count: testRegions.length,
      next: null,
      previous: null,
      results: testRegions,
    }),
  ),

  http.get('*api/shipping/comunas/', ({ request }) => {
    const url = new URL(request.url)
    const regionParam = url.searchParams.get('region')
    const regionId = regionParam ? parseInt(regionParam, 10) : null

    const filtered =
      regionId === null
        ? testComunas
        : testComunas.filter((comuna) => {
            if (regionId === 13) {
              return ['Santiago', 'Providencia'].includes(comuna.name)
            }
            if (regionId === 5) {
              return comuna.name === 'Viña del Mar'
            }
            return false
          })

    return HttpResponse.json({
      count: filtered.length,
      next: null,
      previous: null,
      results: filtered,
    })
  }),
]
