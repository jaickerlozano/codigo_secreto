import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import type { AddressSchema } from '../../schemas/checkout.schema'

import { StepAddress } from './StepAddress'

const emptyAddress: AddressSchema = {
  regionId: 0,
  regionName: '',
  comunaId: 0,
  comunaName: '',
  address: '',
  apartment: '',
  postalCode: '',
  notes: '',
}

function renderStepAddress(onSubmit = vi.fn()) {
  const user = userEvent.setup()
  render(
    <QueryClientProvider client={queryClient()}>
      <StepAddress
        defaultValues={emptyAddress}
        onSubmit={onSubmit}
        onBack={vi.fn()}
      />
    </QueryClientProvider>
  )
  return { user, onSubmit }
}

async function pickRegion(
  user: ReturnType<typeof userEvent.setup>,
  name: string
) {
  const trigger = screen.getByRole('combobox', { name: /Región/ })
  await waitFor(() => expect(trigger.hasAttribute('disabled')).toBe(false))
  await user.click(trigger)
  await user.click(await screen.findByRole('option', { name }))
}

async function pickComuna(
  user: ReturnType<typeof userEvent.setup>,
  name: string
) {
  const trigger = screen.getByRole('combobox', { name: /Comuna/ })
  await waitFor(() => expect(trigger.hasAttribute('disabled')).toBe(false))
  await user.click(trigger)
  await user.click(await screen.findByRole('option', { name }))
}

describe('StepAddress region/comuna controls', () => {
  it('renders both triggers with placeholder text, chevron and required semantics', async () => {
    renderStepAddress()

    const regionTrigger = screen.getByRole('combobox', { name: /Región/ })
    const comunaTrigger = screen.getByRole('combobox', { name: /Comuna/ })

    await waitFor(() =>
      expect(regionTrigger.textContent).toContain('Seleccionar...')
    )
    expect(comunaTrigger.textContent).toContain('Selecciona una región primero')
    expect(regionTrigger.querySelector('svg')).not.toBeNull()
    expect(comunaTrigger.querySelector('svg')).not.toBeNull()
    expect(regionTrigger.getAttribute('aria-required')).toBe('true')
    expect(comunaTrigger.getAttribute('aria-required')).toBe('true')
  })

  it('selects region and comuna and submits numeric ids with their names', async () => {
    const { user, onSubmit } = renderStepAddress()

    await pickRegion(user, 'Región Metropolitana')
    await pickComuna(user, 'Santiago')
    await user.type(
      screen.getByLabelText(/Calle y número/),
      'Av. Siempre Viva 123'
    )
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        regionId: 13,
        regionName: 'Región Metropolitana',
        comunaId: 1,
        comunaName: 'Santiago',
      }),
      expect.anything()
    )
  })

  it('resets comuna before exposing the new cascade when region changes', async () => {
    const { user, onSubmit } = renderStepAddress()

    await pickRegion(user, 'Región Metropolitana')
    await pickComuna(user, 'Santiago')
    expect(
      screen.getByRole('combobox', { name: /Comuna/ }).textContent
    ).toContain('Santiago')

    await pickRegion(user, 'Valparaíso')

    const comunaTrigger = screen.getByRole('combobox', { name: /Comuna/ })
    await waitFor(() =>
      expect(comunaTrigger.textContent).toContain('Seleccionar...')
    )
    await user.click(comunaTrigger)
    await user.click(
      await screen.findByRole('option', { name: 'Viña del Mar' })
    )
    await user.type(
      screen.getByLabelText(/Calle y número/),
      'Av. Siempre Viva 123'
    )
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        regionId: 5,
        regionName: 'Valparaíso',
        comunaId: 3,
        comunaName: 'Viña del Mar',
      }),
      expect.anything()
    )
  })

  it('shows a loading status on comuna while its cascade loads', async () => {
    let releaseComunas: () => void = () => {}
    const gate = new Promise<void>((resolve) => {
      releaseComunas = resolve
    })
    server.use(
      http.get(/\/api\/shipping\/comunas\/$/, () =>
        gate.then(() =>
          HttpResponse.json({
            count: 2,
            next: null,
            previous: null,
            results: [
              { id: 1, name: 'Santiago', shipping_cost: 3500, is_active: true },
              {
                id: 2,
                name: 'Providencia',
                shipping_cost: 3500,
                is_active: true,
              },
            ],
          })
        )
      )
    )
    const { user } = renderStepAddress()

    await pickRegion(user, 'Región Metropolitana')
    const comunaTrigger = screen.getByRole('combobox', { name: /Comuna/ })
    expect(comunaTrigger.hasAttribute('disabled')).toBe(true)
    expect(comunaTrigger.textContent).toContain('Cargando comunas...')

    releaseComunas()
    await waitFor(() =>
      expect(comunaTrigger.hasAttribute('disabled')).toBe(false)
    )
  })

  it('shows an alert with retry when regions fail to load', async () => {
    // The query client retries once, so both attempts must fail before the
    // error state surfaces.
    let failRegions = 2
    server.use(
      http.get(/\/api\/shipping\/regions\/$/, () => {
        if (failRegions > 0) {
          failRegions -= 1
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json({
          count: 2,
          next: null,
          previous: null,
          results: [
            { id: 13, name: 'Región Metropolitana', ordinal_number: 7 },
            { id: 5, name: 'Valparaíso', ordinal_number: 4 },
          ],
        })
      })
    )
    const { user } = renderStepAddress()

    expect(
      (await screen.findByRole('alert', undefined, { timeout: 5000 }))
        .textContent
    ).toContain('No se pudieron cargar las regiones')
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    await pickRegion(user, 'Valparaíso')
    expect(
      screen.getByRole('combobox', { name: /Región/ }).textContent
    ).toContain('Valparaíso')
  })

  it('shows an alert with retry when comunas fail to load', async () => {
    // The query client retries once, so both attempts must fail before the
    // error state surfaces.
    let failComunas = 2
    server.use(
      http.get(/\/api\/shipping\/comunas\/$/, () => {
        if (failComunas > 0) {
          failComunas -= 1
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json({
          count: 1,
          next: null,
          previous: null,
          results: [
            { id: 1, name: 'Santiago', shipping_cost: 3500, is_active: true },
          ],
        })
      })
    )
    const { user } = renderStepAddress()

    await pickRegion(user, 'Región Metropolitana')
    expect(
      (await screen.findByRole('alert', undefined, { timeout: 5000 }))
        .textContent
    ).toContain('No se pudieron cargar las comunas')
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    await pickComuna(user, 'Santiago')
    expect(
      screen.getByRole('combobox', { name: /Comuna/ }).textContent
    ).toContain('Santiago')
  })

  it('shows an accessible empty state and keeps comuna disabled when no comunas match', async () => {
    server.use(
      http.get(/\/api\/shipping\/comunas\/$/, () =>
        HttpResponse.json({ count: 0, next: null, previous: null, results: [] })
      )
    )
    const { user } = renderStepAddress()

    await pickRegion(user, 'Región Metropolitana')
    expect((await screen.findByRole('status')).textContent).toContain(
      'No hay comunas disponibles'
    )
    expect(
      screen.getByRole('combobox', { name: /Comuna/ }).hasAttribute('disabled')
    ).toBe(true)
  })

  it('shows an accessible empty state when no regions are available', async () => {
    server.use(
      http.get(/\/api\/shipping\/regions\/$/, () =>
        HttpResponse.json({ count: 0, next: null, previous: null, results: [] })
      )
    )
    renderStepAddress()

    expect((await screen.findByRole('status')).textContent).toContain(
      'No hay regiones disponibles'
    )
    expect(
      screen.getByRole('combobox', { name: /Región/ }).hasAttribute('disabled')
    ).toBe(true)
  })

  it('keeps Radix-standard listbox, keyboard and typeahead behavior', async () => {
    const { user, onSubmit } = renderStepAddress()
    const regionTrigger = screen.getByRole('combobox', { name: /Región/ })
    await waitFor(() =>
      expect(regionTrigger.hasAttribute('disabled')).toBe(false)
    )

    regionTrigger.focus()
    await user.keyboard('{Enter}')
    expect(await screen.findByRole('listbox')).toBeDefined()
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('listbox')).toBeNull())

    await user.keyboard(' ')
    expect(await screen.findByRole('listbox')).toBeDefined()
    await user.keyboard('v')
    expect(
      screen
        .getByRole('option', { name: 'Valparaíso' })
        .hasAttribute('data-highlighted')
    ).toBe(true)
    await user.keyboard('{Enter}')
    expect(regionTrigger.textContent).toContain('Valparaíso')

    await pickComuna(user, 'Viña del Mar')
    await user.type(
      screen.getByLabelText(/Calle y número/),
      'Av. Siempre Viva 123'
    )
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ regionId: 5, comunaId: 3 }),
      expect.anything()
    )
  })
})
