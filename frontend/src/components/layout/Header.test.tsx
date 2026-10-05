import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, MemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '@/features/auth/context/AuthContext'
import type { Category } from '@/features/catalog/types'
import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { Header } from './Header'

const TEST_CATEGORIES: Category[] = [
  { id: 1, name: 'Vibradores', icon: '✦', gradient: 'from-violet-900 to-purple-700' },
  { id: 2, name: 'Lubricantes', icon: '◇', gradient: 'from-amber-900 to-yellow-700' },
  { id: 3, name: 'Juegos', icon: '❋', gradient: 'from-lime-900 to-emerald-700' },
]

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient()}>
      <AuthProvider>
        <MemoryRouter>{children}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

async function renderSearch(initialEntries: string[], mobile = false) {
  const router = createMemoryRouter(
    [{ path: '*', element: <Header categories={TEST_CATEGORIES} /> }],
    { initialEntries },
  )
  const u = userEvent.setup()
  render(
    <QueryClientProvider client={queryClient()}>
      <AuthProvider><RouterProvider router={router} /></AuthProvider>
    </QueryClientProvider>,
  )
  if (mobile) await u.click(screen.getByRole('button', { name: 'Abrir menú' }))
  const input = screen.getByRole('searchbox', { name: mobile ? 'Buscar' : 'Buscar productos' }) as HTMLInputElement
  const form = input.closest('form') as HTMLFormElement
  return { router, u, input, form }
}

const searchModes = [
  { name: 'desktop', mobile: false },
  { name: 'mobile', mobile: true },
]

describe.each(searchModes)('Header $name search', ({ mobile }) => {
  it('hydrates direct URLs and keeps nonempty typing as a shared draft until Enter', async () => {
    const { router, u, input } = await renderSearch(['/category/todos?search=juguete%20nuevo'], mobile)
    expect(input.value).toBe('juguete nuevo')
    await u.type(input, '+extra')
    expect(router.state.location.search).toBe('?search=juguete%20nuevo')
    if (mobile) {
      expect((screen.getByRole('searchbox', { name: 'Buscar productos' }) as HTMLInputElement).value).toBe('juguete nuevo+extra')
    }
    await u.keyboard('{Enter}')
    expect(router.state.location.pathname).toBe('/category/todos')
    expect(router.state.location.search).toBe('?search=juguete%20nuevo%2Bextra')
    if (mobile) await waitFor(() => expect(screen.queryByRole('searchbox', { name: 'Buscar' })).toBeNull())
  })

  it('submits trimmed nonempty drafts with the search button', async () => {
    const { router, u, input, form } = await renderSearch(['/contact?view=compact#form'], mobile)
    await u.type(input, ' juguete+nuevo ')
    expect(router.state.location.pathname).toBe('/contact')
    await u.click(within(form).getByRole('button', { name: 'Buscar productos' }))
    expect(router.state.location.pathname).toBe('/category/todos')
    expect(router.state.location.search).toBe('?search=juguete%2Bnuevo')
  })

  it('immediately removes only search on manual empty input and retains focus', async () => {
    const { router, u, input } = await renderSearch(['/category/2?view=a%20b&search=aceite&tag=x&tag=y#results'], mobile)
    await u.clear(input)
    expect(input.value).toBe('')
    expect(router.state.location.pathname).toBe('/category/2')
    expect(router.state.location.search).toBe('?view=a%20b&tag=x&tag=y')
    expect(router.state.location.hash).toBe('#results')
    expect(document.activeElement).toBe(input)
    expect(screen.queryByRole('button', { name: 'Limpiar búsqueda' })).toBeNull()
  })

  it('removes duplicate and encoded search parameters for whitespace-only input', async () => {
    const { router, input } = await renderSearch(['/category/todos?search=uno&view=grid&%73earch=dos#results'], mobile)
    fireEvent.change(input, { target: { value: ' \t ' } })
    expect(input.value).toBe('')
    expect(router.state.location.search).toBe('?view=grid')
    expect(router.state.location.hash).toBe('#results')
  })

  it('clears through X without submitting or closing the mobile menu and focuses the actual input', async () => {
    const { router, u, input, form } = await renderSearch(['/contact?view=a%20b&search=consulta#form'], mobile)
    const clear = within(form).getByRole('button', { name: 'Limpiar búsqueda' })
    expect(clear.getAttribute('type')).toBe('button')
    expect(clear.closest('button[type="submit"]')).toBeNull()
    expect(clear.classList.contains('size-12')).toBe(true)
    await u.click(clear)
    expect(router.state.location.pathname).toBe('/contact')
    expect(router.state.location.search).toBe('?view=a%20b')
    expect(router.state.location.hash).toBe('#form')
    expect(input.value).toBe('')
    expect(document.activeElement).toBe(input)
    if (mobile) expect(screen.getByRole('button', { name: 'Cerrar menú' })).toBeDefined()
  })

  it('supports keyboard activation of clear and returns focus to the input', async () => {
    const { router, u, input, form } = await renderSearch(['/category/todos?search=aceite'], mobile)
    await u.click(input)
    await u.tab()
    expect(document.activeElement).toBe(within(form).getByRole('button', { name: 'Limpiar búsqueda' }))
    await u.keyboard('{Enter}')
    expect(router.state.location.search).toBe('')
    expect(document.activeElement).toBe(input)
  })

  it('clears an unapplied draft on unrelated pages without creating navigation', async () => {
    const { router, u, input, form } = await renderSearch(['/contact?view=compact#form'], mobile)
    const locationKey = router.state.location.key
    await u.type(input, 'borrador')
    await u.click(within(form).getByRole('button', { name: 'Limpiar búsqueda' }))
    expect(router.state.location.key).toBe(locationKey)
    await u.type(input, 'otro')
    await u.clear(input)
    expect(router.state.location.key).toBe(locationKey)
    await u.keyboard('{Enter}')
    expect(router.state.location.key).toBe(locationKey)
  })

  it('syncs back/forward, new queries, unrelated query changes and routes without search', async () => {
    const { router, u, input } = await renderSearch([
      '/category/todos?search=primero',
      '/category/todos?search=segundo',
    ], mobile)
    expect(input.value).toBe('segundo')
    await u.type(input, ' borrador')
    await act(() => router.navigate(-1))
    expect(input.value).toBe('primero')
    await act(() => router.navigate(1))
    expect(input.value).toBe('segundo')
    await act(() => router.navigate('/category/todos?search=tercero'))
    expect(input.value).toBe('tercero')
    await u.type(input, ' borrador')
    await act(() => router.navigate('/category/todos?search=tercero&view=grid'))
    expect(input.value).toBe('tercero')
    await act(() => router.navigate('/contact#form'))
    expect(input.value).toBe('')
  })
})

describe('Header', () => {
  it('renders logo, search, cart, favorites link and category navigation', async () => {
    render(<Header categories={TEST_CATEGORIES} />, {
      wrapper: Wrapper,
    })

    expect(
      screen.getByRole('button', { name: /Código Secreto — Inicio/i }),
    ).toBeDefined()
    expect(
      screen.getAllByRole('link', { name: /Vibradores/i }).length,
    ).toBeGreaterThan(0)
    expect(
      screen.getByRole('button', { name: /Carrito — 0 productos/i }),
    ).toBeDefined()
    expect((await screen.findByRole('link', { name: /Favoritos — 0/i })).getAttribute('href')).toBe('/favorites')
  })

  it('renders mobile menu categories when menu is opened', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)

    for (const category of TEST_CATEGORIES) {
      expect(
        screen.getAllByRole('link', { name: category.name }).length,
      ).toBeGreaterThan(0)
    }
  })

  it('shows Mis pedidos in desktop account dropdown when authenticated', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const accountButton = await screen.findByRole('button', { name: /Mi cuenta/i })
    await u.click(accountButton)
    expect(screen.getByRole('menuitem', { name: /Mis pedidos/i })).toBeDefined()
  })

  it('shows Mis pedidos in mobile menu when authenticated', async () => {
    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })
    await screen.findByRole('button', { name: /Mi cuenta/i })

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)
    expect(
      screen.getAllByRole('link', { name: /Mis pedidos/i }).length,
    ).toBeGreaterThan(0)
  })

  it('hides Mis pedidos from desktop dropdown and mobile menu for guests', async () => {
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () =>
        new HttpResponse(null, { status: 401 }),
      ),
    )

    const userEventModule = await import('@testing-library/user-event')
    const u = userEventModule.default.setup()

    render(<Header categories={TEST_CATEGORIES} />, { wrapper: Wrapper })

    const loginButton = await screen.findByRole('link', { name: /Iniciar sesión/i })
    expect(loginButton).toBeDefined()
    expect(screen.queryByRole('menuitem', { name: /Mis pedidos/i })).toBeNull()
    expect(screen.queryByRole('link', { name: /Mis pedidos/i })).toBeNull()

    const menuButton = screen.getByRole('button', { name: /Abrir menú/i })
    await u.click(menuButton)
    expect(screen.queryByRole('link', { name: /Mis pedidos/i })).toBeNull()
  })
})
