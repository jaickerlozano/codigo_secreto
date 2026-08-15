import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import { routes } from '@/app/router.tsx'
import { FAVORITES_STORAGE_KEY, useFavoritesStore } from '@/features/favorites/store/favoritesStore'
import { SESSION_EXPIRED_EVENT } from '@/lib/api-client'
import { queryClient } from '@/lib/query-client'
import { testUser } from '@/test/handlers/auth'
import { trackedFavorites } from '@/test/handlers/favorites'
import { server } from '@/test/setup'

const FAVORITES_URL = 'http://localhost:8000/api/favorites/'
const apiProduct = (id: number) => ({ id, name: id === 1 ? 'Vibrador de prueba' : 'Aceite de masaje', description: 'Descripción de prueba', current_stock: 10, minimum_stock: 1, price: id === 1 ? 29990 : 15990, image: null, sku: String(id), icon: '✦', gradient: 'from-violet-950 via-purple-900 to-violet-800', experience_level: 3, features: [], badge: null, created_at: '2026-07-09T00:00:00Z', updated_at: '2026-07-09T00:00:00Z', category: 1, supplier: 1 })
const fav = (product: number) => ({ id: product, product, created_at: '2026-08-15T00:00:00Z' })
let meStatus = 401
let client: ReturnType<typeof queryClient>
function renderApp(initialPath: string) {
  window.localStorage.setItem('cs-age-verified', 'true')
  server.use(http.get('http://localhost:8000/api/auth/me/', () => HttpResponse.json(meStatus === 200 ? testUser : { detail: 'no session' }, { status: meStatus })), http.post('http://localhost:8000/api/auth/login/', () => { meStatus = 200; return HttpResponse.json({ access: 'access-token', refresh: 'refresh-token', email: testUser.email, password: '' }) }), http.get('http://localhost:8000/api/products/:id/', ({ params }) => HttpResponse.json(apiProduct(Number(params.id)))))
  render(<QueryClientProvider client={(client = queryClient())}><AuthProvider><RouterProvider router={createMemoryRouter(routes, { initialEntries: [initialPath] })} /></AuthProvider></QueryClientProvider>)
}

describe('favorites runtime harness', () => {
  beforeEach(() => { meStatus = 401 })

  it('shows the empty state with a catalog link (guest)', async () => {
    renderApp('/favorites')
    expect(await screen.findByRole('heading', { name: 'Mis Favoritos' })).toBeDefined(); expect(await screen.findByText('No tienes favoritos todavía.')).toBeDefined(); expect(screen.getByRole('link', { name: 'Explorar productos' }).getAttribute('href')).toBe('/category/todos')
  })
  it('shows a loading status while the session is being resolved', async () => {
    server.use(http.get('http://localhost:8000/api/auth/me/', () => new Promise(() => {})))
    renderApp('/favorites')
    expect((await screen.findByRole('status')).textContent).toContain('Cargando favoritos…')
  })
  it('shows an auth error with retry when session resolution fails, then recovers', async () => {
    meStatus = 500; const user = userEvent.setup()
    renderApp('/favorites')
    expect((await screen.findByRole('alert')).textContent).toContain('No pudimos verificar tu sesión.')
    meStatus = 200
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('No tienes favoritos todavía.')).toBeDefined()
  })
  it('shows a loading status while authenticated favorites are fetched', async () => {
    meStatus = 200; server.use(http.get(FAVORITES_URL, () => new Promise(() => {})))
    renderApp('/favorites')
    expect((await screen.findByRole('status')).textContent).toContain('Cargando favoritos…')
  })
  it('shows an error with retry when the authenticated list fails, then recovers', async () => {
    meStatus = 200; let failures = 2; server.use(http.get(FAVORITES_URL, () => (failures-- > 0 ? HttpResponse.json({ detail: 'boom' }, { status: 500 }) : HttpResponse.json([fav(1)])))); const user = userEvent.setup()
    renderApp('/favorites')
    expect((await screen.findByRole('alert', undefined, { timeout: 5000 })).textContent).toContain('No pudimos cargar tus favoritos.')
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('Vibrador de prueba')).toBeDefined()
  })
  it('removes an authenticated favorite through the backend and refreshes the list', async () => {
    meStatus = 200; trackedFavorites.push(fav(1), fav(2)); const user = userEvent.setup()
    renderApp('/favorites')
    await user.click(await screen.findByRole('button', { name: /Quitar Vibrador de prueba de favoritos/i }))
    await waitFor(() => expect(screen.queryByText('Vibrador de prueba')).toBeNull()); expect(screen.getByText('Aceite de masaje')).toBeDefined()
    expect(trackedFavorites.map((f) => f.product)).toEqual([2])
    await user.click(screen.getByRole('button', { name: /Quitar Aceite de masaje de favoritos/i }))
    await waitFor(() => expect(trackedFavorites).toEqual([])); expect(await screen.findByText('No tienes favoritos todavía.')).toBeDefined()
  })
  it('surfaces a failed delete with retry that re-runs the removal', async () => {
    meStatus = 200; trackedFavorites.push(fav(1)); let deleteFailures = 1
    server.use(http.delete('http://localhost:8000/api/favorites/:productId/', ({ params }) => (deleteFailures-- > 0 ? HttpResponse.json({ detail: 'boom' }, { status: 500 }) : (trackedFavorites.splice(0, trackedFavorites.length, ...trackedFavorites.filter((f) => f.product !== Number(params.productId))), new HttpResponse(null, { status: 204 }))))); const user = userEvent.setup()
    renderApp('/favorites')
    await user.click(await screen.findByRole('button', { name: /Quitar Vibrador de prueba de favoritos/i }))
    expect((await screen.findByRole('alert')).textContent).toContain('No pudimos quitar el favorito.')
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    await waitFor(() => expect(trackedFavorites).toEqual([]))
    expect(await screen.findByText('No tienes favoritos todavía.')).toBeDefined()
  })
  it('guest count → login merge (storage cleared) → auth count → authenticated list', async () => {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1, 2])); useFavoritesStore.getState().initFromStorage(); const user = userEvent.setup()
    renderApp('/')
    await user.click(await screen.findByRole('link', { name: /Favoritos — 2/i })); expect(await screen.findByRole('heading', { name: 'Mis Favoritos' })).toBeDefined(); expect(await screen.findByText('Vibrador de prueba')).toBeDefined()
    await user.click(screen.getByRole('button', { name: /Quitar Vibrador de prueba de favoritos/i }))
    await waitFor(() => expect(JSON.parse(window.localStorage.getItem(FAVORITES_STORAGE_KEY) ?? '[]')).toEqual([2]))
    await user.click(screen.getByRole('link', { name: /Iniciar sesión/i }))
    await user.type(await screen.findByLabelText(/Correo electrónico/, undefined, { timeout: 5000 }), 'test@example.com'); await user.type(screen.getByLabelText(/Contraseña/), 'supersecret'); await user.click(screen.getByRole('button', { name: /Iniciar sesión/ }))
    await waitFor(() => expect(trackedFavorites.map((f) => f.product)).toEqual([2])); expect(window.localStorage.getItem(FAVORITES_STORAGE_KEY)).toBeNull()
    await user.click(await screen.findByRole('link', { name: /Favoritos — 1/i }))
    expect(await screen.findByText('Aceite de masaje')).toBeDefined()
  })
  it('removes the favorites cache on logout so a later user cannot see them', async () => {
    meStatus = 200
    trackedFavorites.push(fav(1))
    server.use(http.post('http://localhost:8000/api/auth/logout/', () => { meStatus = 401; return HttpResponse.json({ message: 'ok' }) }))
    renderApp('/favorites')
    await screen.findByText('Vibrador de prueba'); expect(client.getQueryData(['favorites'])).toEqual([fav(1)])
    await userEvent.setup().click(screen.getByRole('button', { name: 'Mi cuenta' }))
    await userEvent.setup().click(await screen.findByRole('menuitem', { name: 'Cerrar sesión' }))
    await waitFor(() => expect(client.getQueryData(['favorites'])).toBeUndefined())
  })
  it('removes the favorites cache on session expiration so a later user cannot see them', async () => {
    meStatus = 200
    trackedFavorites.push(fav(1))
    renderApp('/favorites')
    await screen.findByText('Vibrador de prueba'); expect(client.getQueryData(['favorites'])).toEqual([fav(1)])
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    expect(client.getQueryData(['favorites'])).toBeUndefined()
  })
  it('header does not claim a favorite count while the auth list is unresolved', async () => {
    meStatus = 200; server.use(http.get(FAVORITES_URL, () => new Promise(() => {})))
    renderApp('/')
    expect(await screen.findByRole('link', { name: 'Favoritos' }, { timeout: 5000 })).toBeDefined(); expect(screen.queryByRole('link', { name: 'Favoritos — 0' })).toBeNull()
  })
  it('header drops the count instead of showing stale data when the auth list fails', async () => {
    meStatus = 200; let calls = 0; server.use(http.get(FAVORITES_URL, () => (calls++ < 1 ? HttpResponse.json([fav(1)]) : HttpResponse.json({ detail: 'boom' }, { status: 500 }))))
    renderApp('/')
    expect(await screen.findByRole('link', { name: 'Favoritos — 1' }, { timeout: 5000 })).toBeDefined()
    await client.invalidateQueries({ queryKey: ['favorites'] })
    expect(await screen.findByRole('link', { name: 'Favoritos' }, { timeout: 5000 })).toBeDefined(); expect(screen.queryByRole('link', { name: 'Favoritos — 1' })).toBeNull()
  })
  it('header hides the guest count while the session is unresolved', async () => {
    window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1])); useFavoritesStore.getState().initFromStorage(); server.use(http.get('http://localhost:8000/api/auth/me/', () => new Promise(() => {}))); renderApp('/')
    expect(await screen.findByRole('link', { name: 'Favoritos' }, { timeout: 5000 })).toBeDefined(); expect(screen.queryByRole('link', { name: 'Favoritos — 1' })).toBeNull()
  })
  it('header hides the guest count when session resolution fails', async () => {
    meStatus = 500; window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([1])); useFavoritesStore.getState().initFromStorage(); renderApp('/')
    expect(await screen.findByRole('link', { name: 'Favoritos' }, { timeout: 5000 })).toBeDefined(); expect(screen.queryByRole('link', { name: 'Favoritos — 1' })).toBeNull()
  })
  it('header hides the count while the auth list is background-refetching', async () => {
    meStatus = 200; let calls = 0; server.use(http.get(FAVORITES_URL, () => (calls++ < 1 ? HttpResponse.json([fav(1)]) : new Promise(() => {})))); renderApp('/')
    expect(await screen.findByRole('link', { name: 'Favoritos — 1' }, { timeout: 5000 })).toBeDefined()
    void client.invalidateQueries({ queryKey: ['favorites'] })
    expect(await screen.findByRole('link', { name: 'Favoritos' }, { timeout: 5000 })).toBeDefined(); expect(screen.queryByRole('link', { name: 'Favoritos — 1' })).toBeNull()
  })
  it('announces the specific item being removed while the delete is pending', async () => {
    meStatus = 200; trackedFavorites.push(fav(1), fav(2))
    server.use(http.delete('http://localhost:8000/api/favorites/:productId/', () => new Promise(() => {})))
    renderApp('/favorites')
    await userEvent.setup().click(await screen.findByRole('button', { name: /Quitar Vibrador de prueba de favoritos/i }, { timeout: 5000 }))
    const status = await screen.findByRole('status'); expect(status.textContent).toContain('Quitando favorito: Vibrador de prueba'); expect(screen.queryByRole('button', { name: /Quitar Vibrador de prueba de favoritos/i })).toBeNull(); expect(screen.getByRole('button', { name: /Quitar Aceite de masaje de favoritos/i })).toBeDefined()
  })
})
