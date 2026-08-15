import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Favorite = components['schemas']['Favorite']

export let trackedFavorites: Favorite[] = []
export function resetFavoritesHandlers(): void { trackedFavorites = [] }

export const favoritesHandlers = [
  http.get('http://localhost:8000/api/favorites/', () => HttpResponse.json(trackedFavorites)),
  http.post('http://localhost:8000/api/favorites/', async ({ request }) => {
    const { product_ids } = (await request.json()) as components['schemas']['FavoriteMerge']
    product_ids.forEach((productId) => { if (!trackedFavorites.some((f) => f.product === productId)) trackedFavorites.push({ id: productId, product: productId, created_at: '2026-08-15T00:00:00Z' }) })
    return HttpResponse.json(trackedFavorites)
  }),
  http.delete('http://localhost:8000/api/favorites/:productId/', ({ params }) => { trackedFavorites = trackedFavorites.filter((f) => f.product !== Number(params.productId)); return new HttpResponse(null, { status: 204 }) }),
]
