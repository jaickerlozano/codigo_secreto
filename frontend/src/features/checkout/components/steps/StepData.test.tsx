import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'

import type { AddressData, ContactData } from '../../types'

import { StepData } from './StepData'

const contact: ContactData = { name: '', email: '', phone: '', isGuest: true }
const address: AddressData = { regionId: 0, regionName: '', comunaId: 0, comunaName: '', address: '', apartment: '', postalCode: '', notes: '' }

function renderStepData(onSubmit = vi.fn()) {
  const user = userEvent.setup()
  render(<QueryClientProvider client={queryClient()}><StepData defaultValues={{ contact, address }} onSubmit={onSubmit} /></QueryClientProvider>)
  return { user, onSubmit }
}

async function fillContact(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/Nombre completo/), 'Juan Pérez')
  await user.type(screen.getByLabelText(/Email/), 'juan@example.com')
  await user.type(screen.getByLabelText(/Teléfono/), '+56 9 1234 5678')
  await user.click(screen.getByRole('button', { name: /Siguiente/ }))
}

describe('StepData (composed Data step)', () => {
  it('starts at the contact form before the address form', () => {
    renderStepData()

    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(screen.queryByRole('group', { name: 'Dirección de envío' })).toBeNull()
  })

  it('blocks invalid contact data without advancing or submitting', async () => {
    const { user, onSubmit } = renderStepData()

    await user.type(screen.getByLabelText(/Nombre completo/), 'A')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    expect(await screen.findByText('El nombre debe tener al menos 2 caracteres')).toBeDefined()
    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('advances to the address form after valid contact data', async () => {
    const { user } = renderStepData()

    await fillContact(user)

    expect(await screen.findByRole('group', { name: 'Dirección de envío' })).toBeDefined()
  })

  it('submits contact and address together after both are valid', async () => {
    const { user, onSubmit } = renderStepData()

    await fillContact(user)
    const regionSelect = await screen.findByLabelText(/Región/)
    await user.selectOptions(regionSelect, '13')
    const comunaSelect = screen.getByLabelText(/Comuna/)
    await waitFor(() => expect(comunaSelect.querySelector('option[value="1"]')).not.toBeNull())
    await user.selectOptions(comunaSelect, '1')
    await user.type(screen.getByLabelText(/Calle y número/), 'Av. Siempre Viva 123')
    await user.click(screen.getByRole('button', { name: /Siguiente/ }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit).toHaveBeenCalledWith({
      contact: { name: 'Juan Pérez', email: 'juan@example.com', phone: '+56 9 1234 5678', isGuest: true },
      address: expect.objectContaining({ regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Av. Siempre Viva 123' }),
    })
  })

  it('returns from the address form to the contact form via Atrás', async () => {
    const { user } = renderStepData()

    await fillContact(user)
    await screen.findByRole('group', { name: 'Dirección de envío' })
    await user.click(screen.getByRole('button', { name: 'Atrás' }))

    expect(screen.getByRole('group', { name: 'Datos de contacto' })).toBeDefined()
    expect((screen.getByLabelText(/Nombre completo/) as HTMLInputElement).value).toBe('Juan Pérez')
  })
})
