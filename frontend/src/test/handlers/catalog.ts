import { http, HttpResponse } from 'msw'

const testCategory = {
  id: 1,
  name: 'Vibradores',
  description: '',
  parent: null,
  subcategories: [],
}

const testProduct = {
  id: 1,
  name: 'Vibrador de prueba',
  description: 'Descripción de prueba',
  current_stock: 10,
  minimum_stock: 1,
  price: 29990,
  image: null,
  sku: '101',
  icon: '✦',
  gradient: 'from-violet-950 via-purple-900 to-violet-800',
  experience_level: 3,
  features: [],
  badge: null,
  created_at: '2026-07-09T00:00:00Z',
  updated_at: '2026-07-09T00:00:00Z',
  category: 1,
  supplier: 1,
}

export const catalogHandlers = [
  http.get('http://localhost:8000/api/categories/', () =>
    HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [testCategory],
    }),
  ),

  http.get('http://localhost:8000/api/products/', () =>
    HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [testProduct],
    }),
  ),

  http.get('http://localhost:8000/api/products/:id/', () =>
    HttpResponse.json(testProduct),
  ),
]
