import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import { routes } from '@/app/router.tsx'
import { AuthProvider } from '@/features/auth/context/AuthContext'
import { queryClient } from '@/lib/query-client'
import { trackedContactMessages } from '@/test/handlers/contact'
import { server } from '@/test/setup'

// jsdom provides no layout APIs: Radix Slider renders `calc(NaN% + 0px)` and
// throws a CSS parse error, and ResizeObserver is undefined. The Slider is
// UI chrome irrelevant to the flows under test, so it is stubbed here.
vi.mock('@/components/ui/slider', () => ({ Slider: () => <div /> }))
class ResizeObserverStub { observe() { void 0 } unobserve() { void 0 } disconnect() { void 0 } }
beforeAll(() => { (globalThis as Record<string, unknown>).ResizeObserver = ResizeObserverStub })

const CONTACT_URL = 'http://localhost:8000/api/contact/'
const PRODUCTS_URL = 'http://localhost:8000/api/products/'
const apiProduct = { id: 1, name: 'Vibrador de prueba', description: 'Descripción de prueba', current_stock: 10, minimum_stock: 1, price: 29990, image: null, sku: '101', icon: '✦', gradient: 'from-violet-950 via-purple-900 to-violet-800', experience_level: 3, features: [], badge: null, created_at: '2026-07-09T00:00:00Z', updated_at: '2026-07-09T00:00:00Z', category: 1, supplier: 1 }

function renderApp(initialPath: string) {
  window.localStorage.setItem('cs-age-verified', 'true')
  render(<QueryClientProvider client={queryClient()}><AuthProvider><RouterProvider router={createMemoryRouter(routes, { initialEntries: [initialPath] })} /></AuthProvider></QueryClientProvider>)
}
const user = () => userEvent.setup()
async function fillForm(u: ReturnType<typeof userEvent.setup>) {
  await u.type(await screen.findByLabelText(/Nombre/), 'Cliente Test')
  await u.type(screen.getByLabelText(/Email/), 'cliente@example.com')
  await u.type(screen.getByLabelText(/Asunto/), 'Consulta sobre un producto')
  await u.type(screen.getByLabelText(/Mensaje/), 'Quisiera saber el tiempo de despacho a Temuco.')
}

describe('contact runtime harness', () => {
  it('shows client validation errors for empty required fields without sending anything', async () => {
    const u = user()
    renderApp('/contact')
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    const alerts = await screen.findAllByRole('alert')
    expect(['El nombre es obligatorio', 'El email es obligatorio', 'El asunto es obligatorio', 'El mensaje es obligatorio'].every((m) => alerts.some((a) => a.textContent?.includes(m)))).toBe(true)
    expect(trackedContactMessages).toHaveLength(0)
  })
  it('shows an inline error for an invalid email', async () => {
    const u = user()
    renderApp('/contact')
    await u.type(await screen.findByLabelText(/Nombre/), 'Cliente Test')
    await u.type(screen.getByLabelText(/Email/), 'no-es-email')
    await u.type(screen.getByLabelText(/Asunto/), 'Consulta')
    await u.type(screen.getByLabelText(/Mensaje/), 'Hola, quisiera hacer una consulta.')
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    const alerts = await screen.findAllByRole('alert')
    expect(alerts.some((a) => a.textContent?.includes('Ingresa un email válido'))).toBe(true)
    expect(trackedContactMessages).toHaveLength(0)
  })
  it('shows a pending status and disables submit while the message is being sent', async () => {
    server.use(http.post(CONTACT_URL, () => new Promise(() => {})))
    const u = user()
    renderApp('/contact')
    await fillForm(u)
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    expect((await screen.findByRole('status')).textContent).toContain('Enviando mensaje…')
    expect((screen.getByRole('button', { name: /Enviando/ }) as HTMLButtonElement).disabled).toBe(true)
  })
  it('shows the success state with the message id and allows sending another', async () => {
    const u = user()
    renderApp('/contact')
    await fillForm(u)
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    expect(await screen.findByText(/Tu mensaje fue recibido/)).toBeDefined()
    expect((screen.getByRole('status')).textContent).toContain('mensaje #1')
    expect(trackedContactMessages).toHaveLength(1)
    expect(trackedContactMessages[0].email).toBe('cliente@example.com')
    await u.click(screen.getByRole('button', { name: /Enviar otro mensaje/ }))
    expect(await screen.findByLabelText(/Nombre/)).toBeDefined()
  })
  it('surfaces server field validation errors inline and keeps the form values', async () => {
    server.use(http.post(CONTACT_URL, () => HttpResponse.json({ email: ['El email ingresado no es válido para contacto.'] }, { status: 400 })))
    const u = user()
    renderApp('/contact')
    await fillForm(u)
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    const alerts = await screen.findAllByRole('alert')
    expect(alerts.some((a) => a.textContent?.includes('Revisa los campos marcados.'))).toBe(true)
    expect(alerts.some((a) => a.textContent?.includes('El email ingresado no es válido para contacto.'))).toBe(true)
    expect(screen.queryByRole('button', { name: 'Reintentar' })).toBeNull()
    expect((screen.getByLabelText(/Email/) as HTMLInputElement).value).toBe('cliente@example.com')
    expect(trackedContactMessages).toHaveLength(0)
  })
  it('surfaces a throttle failure with the server message and a retry affordance', async () => {
    server.use(http.post(CONTACT_URL, () => HttpResponse.json({ detail: 'Demasiados intentos. Intenta nuevamente en 60 minutos.' }, { status: 429 })))
    const u = user()
    renderApp('/contact')
    await fillForm(u)
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    expect((await screen.findByRole('alert')).textContent).toContain('Demasiados intentos. Intenta nuevamente en 60 minutos.')
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeDefined()
    expect(trackedContactMessages).toHaveLength(0)
  })
  it('shows a generic failure and resubmits safely on retry without duplicates', async () => {
    let calls = 0
    server.use(http.post(CONTACT_URL, async ({ request }) => { calls++; if (calls === 1) return HttpResponse.json({ detail: 'boom' }, { status: 500 }); trackedContactMessages.push((await request.json()) as Record<string, unknown>); return HttpResponse.json({ id: 1, status: 'NEW' }, { status: 201 }) }))
    const u = user()
    renderApp('/contact')
    await fillForm(u)
    await u.click(screen.getByRole('button', { name: /Enviar mensaje/ }))
    expect((await screen.findByRole('alert')).textContent).toContain('Error del servidor. Intenta más tarde.')
    await u.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText(/Tu mensaje fue recibido/)).toBeDefined()
    expect(trackedContactMessages).toHaveLength(1)
  })
  it('wires the existing header Contacto affordances to the /contact route', async () => {
    const u = user()
    renderApp('/')
    const desktop = screen.getAllByRole('link', { name: 'Contacto' })
    expect(desktop).toHaveLength(1)
    expect(desktop[0].getAttribute('href')).toBe('/contact')
    await u.click(screen.getByRole('button', { name: 'Abrir menú' }))
    expect(screen.getAllByRole('link', { name: 'Contacto' })).toHaveLength(2)
    await u.click(screen.getAllByRole('link', { name: 'Contacto' })[1])
    expect(await screen.findByRole('heading', { level: 1, name: 'Contacto' })).toBeDefined()
  })
})

describe('search navigation regression', () => {
  it('header search submit navigates to /category/todos with the encoded query and forwards it to the products API', async () => {
    let lastSearch: string | null = null
    server.use(http.get(PRODUCTS_URL, ({ request }) => { lastSearch = new URL(request.url).searchParams.get('search'); return HttpResponse.json({ count: 1, next: null, previous: null, results: [apiProduct] }) }))
    const u = user()
    renderApp('/')
    const input = await screen.findByLabelText(/Buscar productos/)
    await u.type(input, 'vibrador+nuevo')
    fireEvent.submit(input.closest('form') as HTMLFormElement)
    expect(await screen.findByRole('heading', { name: 'Todos los productos' })).toBeDefined()
    expect(await screen.findByText('Vibrador de prueba')).toBeDefined()
    expect(lastSearch).toBe('vibrador+nuevo')
  })
  it('category page forwards the search parameter from the URL to the products API', async () => {
    let lastSearch: string | null = null
    server.use(http.get(PRODUCTS_URL, ({ request }) => { lastSearch = new URL(request.url).searchParams.get('search'); return HttpResponse.json({ count: 1, next: null, previous: null, results: [apiProduct] }) }))
    renderApp('/category/todos?search=juguete%20nuevo')
    expect(await screen.findByText('Vibrador de prueba')).toBeDefined()
    expect(lastSearch).toBe('juguete nuevo')
  })
})
